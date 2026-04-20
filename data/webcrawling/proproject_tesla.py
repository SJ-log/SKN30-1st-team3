from bs4 import BeautifulSoup
import pandas as pd


class FAQ:
    def __init__(self, question, answer):
        self.question = question
        self.answer = answer

    def __str__(self):
        return f"Q: {self.question}\nA: {self.answer}\n"

    def to_dict(self):
        return {
            "question": self.question,
            "answer": self.answer,
        }


def load_html(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def extract_text_lines(html):
    soup = BeautifulSoup(html, "html.parser")
    full_text = soup.get_text(separator="\n")
    lines = [line.strip() for line in full_text.splitlines() if line.strip()]
    return lines


def get_faq_section(lines):
    start_marker = "Frequently Asked Questions"
    end_marker = "Article Menu"

    start_idx = lines.index(start_marker) if start_marker in lines else 0
    end_idx = lines.index(end_marker) if end_marker in lines else len(lines)

    faq_lines = lines[start_idx:end_idx]

    remove_exact = {
        "Frequently Asked Questions",
        "Answers to frequently asked questions about our order process.",
        "Show All",
        "Hide All",
        "Order",
        "Incentives",
        "Tesla Account",
        "Preparing for Delivery",
        "Financing",
        "Insurance",
        "Charging Solutions",
        "Service and Warranties",
    }

    faq_lines = [line for line in faq_lines if line not in remove_exact]
    return faq_lines


def parse_faqs(faq_lines):
    faq_list = []

    i = 0
    while i < len(faq_lines):
        line = faq_lines[i]

        if "?" in line:
            question = line.lstrip("* ").strip()
            answer_parts = []

            j = i + 1
            while j < len(faq_lines):
                next_line = faq_lines[j]

                if "?" in next_line:
                    break

                answer_parts.append(next_line)
                j += 1

            answer = " ".join(answer_parts).strip()

            if answer:
                faq_list.append(FAQ(question, answer))

            i = j
        else:
            i += 1

    return faq_list


def save_to_csv(faq_list, output_path):
    df = pd.DataFrame([faq.to_dict() for faq in faq_list])
    df = df.drop_duplicates(subset=["question", "answer"]).reset_index(drop=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")


def main():
    html_file_path = r"C:\Users\playdata2\workspace\crawling\tesla_faq.html"
    output_file = "tesla_faq.csv"

    html = load_html(html_file_path)
    lines = extract_text_lines(html)
    faq_lines = get_faq_section(lines)
    faq_list = parse_faqs(faq_lines)

    print(f"수집된 FAQ 개수: {len(faq_list)}\n")

    for faq in faq_list[:5]:
        print(faq)

    save_to_csv(faq_list, output_file)
    print(f"CSV 저장 완료: {output_file}")


if __name__ == "__main__":
    main()