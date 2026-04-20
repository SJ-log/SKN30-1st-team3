import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException


def get_question_elements(driver):
    """
    페이지 전체 FAQ를 하나의 긴 목록처럼 보고,
    클릭 가능한 질문 요소를 순서대로 수집한다.
    """
    selectors = [
        "#faq-accordion-one > div > div.panel-heading > div > p",   # 좌측 형태
        "div.help-content-panel",                                   # 우측 형태
    ]

    elements = []
    seen = set()

    for selector in selectors:
        found = driver.find_elements(By.CSS_SELECTOR, selector)
        for el in found:
            try:
                text = el.text.strip()
                if not text:
                    continue

                # 중복 제거: 같은 질문 텍스트는 한 번만
                if text not in seen:
                    elements.append(el)
                    seen.add(text)
            except StaleElementReferenceException:
                continue

    return elements


def extract_answer_from_question(driver, question_el):
    """
    질문 요소를 클릭한 뒤, 연결된 답변을 최대한 안정적으로 찾는다.
    """
    answer = ""

    # 1) 스크롤 + 클릭
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", question_el)
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", question_el)
    time.sleep(1)

    # 2) 가장 가까운 FAQ 블록 찾기
    container = None
    xpath_candidates = [
        "./ancestor::div[contains(@class, 'panel')][1]",
        "./ancestor::div[contains(@class, 'faq')][1]",
        "./ancestor::div[contains(@class, 'help')][1]",
        "./ancestor::div[1]",
    ]

    for xp in xpath_candidates:
        try:
            container = question_el.find_element(By.XPATH, xp)
            if container:
                break
        except NoSuchElementException:
            continue

    # 3) 같은 블록 안의 답변 후보 탐색
    if container is not None:
        answer_selectors = [
            "div.panel-collapse",
            "div[id^='faqitem']",
            "div.collapse.in",
            "div.collapse.show",
            "div.faq_con",
            "div.panel-body",
            "div.help-content-answer",
            "div > p:nth-child(2)",
        ]

        for selector in answer_selectors:
            try:
                candidates = container.find_elements(By.CSS_SELECTOR, selector)
                texts = [x.text.strip() for x in candidates if x.text.strip()]
                if texts:
                    answer = " ".join(texts).strip()
                    if answer:
                        return answer
            except Exception:
                continue

    # 4) 연결된 collapse/faqitem 찾기
    attr_candidates = ["aria-controls", "data-target", "href"]

    for attr in attr_candidates:
        try:
            ref = question_el.get_attribute(attr)
            if not ref:
                continue

            ref = ref.strip()
            if ref.startswith("#"):
                ref = ref[1:]

            if ref:
                target = driver.find_element(By.ID, ref)
                answer = target.text.strip()
                if answer:
                    return answer
        except Exception:
            continue

    # 5) 질문 다음 형제 요소에서 답변 탐색
    xpath_answer_candidates = [
        "following::div[contains(@id, 'faqitem')][1]",
        "following::div[contains(@class, 'panel-collapse')][1]",
        "following::div[contains(@class, 'faq_con')][1]",
        "following::div[1]",
    ]

    for xp in xpath_answer_candidates:
        try:
            target = question_el.find_element(By.XPATH, xp)
            text = target.text.strip()
            if text:
                return text
        except Exception:
            continue

    return answer


def extract_all_faq(driver):
    data = []

    questions = get_question_elements(driver)
    print(f"찾은 질문 수: {len(questions)}")

    for i in range(len(questions)):
        try:
            # stale 방지: 매번 다시 수집
            questions = get_question_elements(driver)
            question_el = questions[i]

            question = question_el.text.strip()
            if not question:
                continue

            answer = extract_answer_from_question(driver, question_el)

            if question and answer:
                data.append({
                    "question": question,
                    "answer": answer
                })

            print(f"[{i+1}/{len(questions)}] 완료: {question[:50]}")

        except Exception as e:
            print(f"[{i+1}] 처리 실패: {e}")
            continue

    return data


def main():
    driver = webdriver.Chrome()
    url = "https://www.pse.com/ko/pages/electric-cars/electric-vehicles-faq"
    driver.get(url)
    time.sleep(3)

    data = extract_all_faq(driver)

    df = pd.DataFrame(data)
    df = df.drop_duplicates(subset=["question", "answer"]).reset_index(drop=True)

    output_file = "pse_faq_one_column.csv"
    df.to_csv(output_file, index=False, encoding="utf-8-sig")

    print(f"\n수집 완료: {len(df)}개")
    print(f"CSV 저장 완료: {output_file}")

    print("\n샘플 데이터:")
    print(df.head())

    driver.quit()


if __name__ == "__main__":
    main()