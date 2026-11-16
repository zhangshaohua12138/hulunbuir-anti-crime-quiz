FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home quiz && mkdir /data && chown quiz:quiz /data
COPY --chown=quiz:quiz server.py wechat_pay.py ./
COPY --chown=quiz:quiz static ./static
USER quiz
ENV HOST=0.0.0.0 PORT=8080 DATABASE_PATH=/data/quiz.db APP_MODE=production
EXPOSE 8080
VOLUME ["/data"]
CMD ["python", "server.py"]
