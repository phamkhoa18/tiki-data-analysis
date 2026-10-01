# DANH SÁCH TÀI LIỆU THAM KHẢO (REFERENCES)
## Đề tài: Phân tích hệ thống dữ liệu thương mại điện tử TIKI

Dưới đây là danh mục các bài báo khoa học, giáo trình đại học, sách chuyên khảo và tài liệu kỹ thuật được nhóm tham khảo và trích dẫn trong quá trình nghiên cứu và phát triển đồ án:

---

### I. Sách chuyên khảo & Giáo trình (Books & Textbooks)

1. **Zaharia, M., Chambers, B.** (2018). *Spark: The Definitive Guide - Big Data Processing Made Simple*. O'Reilly Media. ISBN: 978-1491912218.
   - *Giá trị tham khảo:* Kiến trúc lõi của Apache Spark, Catalyst Optimizer, cấu trúc dữ liệu DataFrame/Dataset, và triển khai Spark MLlib trên cụm phân tán.

2. **Kleppmann, M.** (2017). *Designing Data-Intensive Applications: The Big Ideas Behind Reliable, Scalable, and Maintainable Systems*. O'Reilly Media. ISBN: 978-1449373320.
   - *Giá trị tham khảo:* Thiết kế kiến trúc Lambda/Kappa, mô hình Data Lake, xử lý luồng sự kiện (Event Streaming) với Kafka và đảm bảo tính nhất quán của dữ liệu.

3. **Leskovec, J., Rajaraman, A., & Ullman, J. D.** (2020). *Mining of Massive Datasets* (3rd ed.). Cambridge University Press.
   - *Giá trị tham khảo:* Các thuật toán gợi ý (Recommendation Systems), kỹ thuật phân rã ma trận (Matrix Factorization) và phân cụm dữ liệu quy mô lớn (Clustering algorithms).

4. **Jurafsky, D., & Martin, J. H.** (2023). *Speech and Language Processing* (3rd ed. draft). Stanford University.
   - *Giá trị tham khảo:* Phương pháp xử lý ngôn ngữ tự nhiên (NLP), phân tích cảm xúc (Sentiment Analysis), trích xuất đặc trưng văn bản bằng TF-IDF và Word Embeddings.

---

### II. Bài báo khoa học & Hội nghị quốc tế (Research Papers)

5. **Koren, Y., Bell, R., & Volinsky, C.** (2009). "Matrix Factorization Techniques for Recommender Systems". *Computer*, 42(8), pp. 30-37. IEEE.
   - *DOI:* `10.1109/MC.2009.263`
   - *Giá trị tham khảo:* Cơ sở lý thuyết của thuật toán ALS (Alternating Least Squares) được áp dụng trên tập dữ liệu đánh giá sản phẩm của Tiki.

6. **Nguyen, D. Q., & Nguyen, A. T.** (2020). "PhoBERT: Pre-trained language models for Vietnamese". *Findings of the Association for Computational Linguistics: EMNLP 2020*, pp. 1037-1042.
   - *Giá trị tham khảo:* Cơ chế tiền xử lý, gán nhãn từ tính và ngữ nghĩa tiếng Việt trên dữ liệu bình luận mua sắm trực tuyến.

7. **Armbrust, M., et al.** (2015). "Spark SQL: Relational Data Processing in Spark". *Proceedings of the 2015 ACM SIGMOD International Conference on Management of Data*, pp. 1383-1394.
   - *Giá trị tham khảo:* Tối ưu hóa truy vấn truy cập dữ liệu dạng bảng với Spark SQL.

8. **Hughes, A. M.** (2005). *Strategic Database Marketing: The Masterplan for Starting and Managing a Profitable, Customer-Based Marketing Program*. McGraw-Hill.
   - *Giá trị tham khảo:* Ứng dụng mô hình RFM (Recency, Frequency, Monetary) trong phân khúc khách hàng thương mại điện tử.

---

### III. Tài liệu kỹ thuật & Đặc tả API (Technical Docs & Specifications)

9. **Apache Spark Official Documentation**:
   - URL: https://spark.apache.org/docs/latest/
   - Nội dung: Spark SQL Guide, MLlib Collaborative Filtering, Structured Streaming Programming Guide.

10. **Apache Kafka Documentation**:
    - URL: https://kafka.apache.org/documentation/
    - Nội dung: Kiến trúc Producer, Consumer Group, Partitioning, Topics, Stream Processing.

11. **Tiki Open Web API Documentation**:
    - URL: https://tiki.vn/
    - Endpoint tham khảo:
      - `GET https://tiki.vn/api/v2/products`: Lấy danh sách sản phẩm theo danh mục và bộ lọc.
      - `GET https://tiki.vn/api/v2/reviews`: Lấy danh sách đánh giá của khách hàng, điểm số sao và bình luận chi tiết.

12. **Parquet Apache Documentation**:
    - URL: https://parquet.apache.org/docs/
    - Nội dung: Định dạng lưu trữ dạng cột (Columnar Storage), kỹ thuật nén Snappy và nén từ điển (Dictionary Encoding) cho Data Lakehouse.
