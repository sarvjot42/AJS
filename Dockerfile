FROM openjdk:8

# Install Python 2
RUN apt-get update && apt-get install -y python2.7

# Set the Python 2 symlink
RUN ln -s /usr/bin/python2.7 /usr/bin/python

# Set environment variables for Java
ENV JAVA_HOME=/usr/local/openjdk-8
ENV PATH=$PATH:$JAVA_HOME/bin

# Set environment variable for Python
ENV PYTHON=/usr/bin/python

COPY ajs/ /ajs/
COPY testcode/ /testcode/

WORKDIR /testcode/

RUN javac TestCode.java
CMD ["java", "TestCode"]
