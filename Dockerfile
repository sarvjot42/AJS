FROM openjdk:11-jdk-slim
COPY TestCode.java .
RUN javac TestCode.java
CMD ["java", "TestCode"]

FROM python:3.9-slim-buster
COPY qst.py .