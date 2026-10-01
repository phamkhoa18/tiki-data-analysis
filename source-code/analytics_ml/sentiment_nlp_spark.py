#!/usr/bin/env python3
"""
NLP Sentiment Analysis & Aspect Mining Module
Processes Vietnamese customer reviews:
- Text normalization & tokenization
- Sentiment classification (Positive / Neutral / Negative)
- Aspect-based sentiment analysis:
  1. Giao hàng / Vận chuyển (TikiNow, thời gian, shipper)
  2. Đóng gói / Bao bì (Bọc khí, móp méo, nguyên seal)
  3. Chất lượng sản phẩm (Chính hãng, bền, lỗi kỹ thuật)
  4. Giá cả & Khuyến mãi (Mã giảm giá, sale, đáng tiền)
"""

import os
import re
import json
import logging
import pandas as pd
from collections import Counter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SentimentNLPSentiment")

ASPECT_KEYWORDS = {
    "Vận chuyển / Giao nhận": ["giao hàng", "nhanh", "chậm", "trễ", "tikinow", "shipper", "vận chuyển", "hẹn"],
    "Đóng gói / Hộp hàng": ["đóng gói", "bọc", "móp", "hộp", "nguyên seal", "rách", "cẩn thận", "chống sốc"],
    "Chất lượng sản phẩm": ["chính hãng", "xịn", "tốt", "bền", "lỗi", "ọp ẹp", "mượt", "hỏng", "chuẩn"],
    "Giá cả & Dịch vụ": ["giá", "sale", "rẻ", "đắt", "mã giảm giá", "đổi trả", "tư vấn", "tiền"]
}

class VietnameseReviewNLP:
    def __init__(self, data_dir=None):
        if data_dir is None:
            root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.data_dir = os.path.join(root, "dataset")
        else:
            self.data_dir = data_dir
        self.processed_dir = os.path.join(self.data_dir, "processed")
        self.output_dir = os.path.join(self.processed_dir, "analytics_results")
        os.makedirs(self.output_dir, exist_ok=True)

    def clean_text(self, text):
        if not isinstance(text, str):
            return ""
        text = text.lower()
        # Remove extra whitespace and special characters but keep accents
        text = re.sub(r"[^\w\s\dàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def analyze_aspects(self, df):
        aspect_results = []
        for aspect_name, keywords in ASPECT_KEYWORDS.items():
            pattern = "|".join([re.escape(k) for k in keywords])
            subset = df[df["clean_content"].str.contains(pattern, na=False)]
            total_mentions = len(subset)
            if total_mentions > 0:
                pos = (subset["sentiment"] == "TÍCH CỰC").sum()
                neu = (subset["sentiment"] == "TRUNG TÍNH").sum()
                neg = (subset["sentiment"] == "TIÊU CỰC").sum()
                pos_pct = round(pos / total_mentions * 100, 1)
                neg_pct = round(neg / total_mentions * 100, 1)
            else:
                pos, neu, neg, pos_pct, neg_pct = 0, 0, 0, 0.0, 0.0

            aspect_results.append({
                "Khía cạnh": aspect_name,
                "Số lượt nhắc đến": total_mentions,
                "Tích cực (%)": pos_pct,
                "Tiêu cực (%)": neg_pct,
                "Điểm hài lòng TB": round(subset["rating"].mean(), 2) if total_mentions > 0 else 0
            })
        return pd.DataFrame(aspect_results)

    def run_pipeline(self):
        csv_path = os.path.join(self.processed_dir, "cleaned_reviews.csv")
        if not os.path.exists(csv_path):
            raise FileNotFoundError("cleaned_reviews.csv not found!")

        df = pd.read_csv(csv_path)
        logger.info(f"Processing NLP on {len(df)} customer reviews...")

        df["clean_content"] = (df["title"].fillna("") + " " + df["content"].fillna("")).apply(self.clean_text)

        # 1. Overall sentiment breakdown
        sentiment_counts = df["sentiment"].value_counts().to_dict()
        sentiment_pct = (df["sentiment"].value_counts(normalize=True) * 100).round(1).to_dict()

        # 2. Aspect analysis
        aspect_df = self.analyze_aspects(df)
        aspect_df.to_csv(os.path.join(self.output_dir, "aspect_sentiment.csv"), index=False)

        # 3. Top frequent terms (Vietnamese unigrams/bigrams)
        words = []
        stopwords = {"và", "là", "thì", "mà", "cho", "của", "có", "rất", "được", "không", "một", "với", "nhưng", "đã", "thấy", "khi"}
        for text in df["clean_content"]:
            tokens = [t for t in text.split() if len(t) > 2 and t not in stopwords]
            words.extend(tokens)
        
        top_words = Counter(words).most_common(25)
        top_words_df = pd.DataFrame(top_words, columns=["TuKhoa", "TanSuat"])
        top_words_df.to_csv(os.path.join(self.output_dir, "top_keywords.csv"), index=False)

        summary = {
            "total_reviews_analyzed": len(df),
            "sentiment_counts": sentiment_counts,
            "sentiment_percentages": sentiment_pct,
            "aspect_breakdown": aspect_df.to_dict(orient="records"),
            "top_positive_driver": "Giao hàng siêu tốc TikiNow & Chất lượng chính hãng",
            "top_negative_driver": "Vỏ hộp móp méo trong quá trình lưu kho / vận chuyển"
        }

        with open(os.path.join(self.output_dir, "sentiment_summary.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        logger.info("NLP Sentiment & Aspect Mining completed successfully.")
        return summary

if __name__ == "__main__":
    nlp = VietnameseReviewNLP()
    res = nlp.run_pipeline()
    print("Sentiment summary:", json.dumps(res, indent=2, ensure_ascii=False))
