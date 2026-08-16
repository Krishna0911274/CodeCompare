FROM eclipse-temurin:21-jdk

WORKDIR /code

# Create a non-root user
RUN useradd -m coder

# Give coder access to the working directory
RUN chown -R coder:coder /code

# Run as non-root user
USER coder

CMD ["java", "--version"]