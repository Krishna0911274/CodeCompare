FROM python:3.12-slim

WORKDIR /code

# Create a non-root user
RUN useradd -m -u 1000 coder

# Give the user ownership of the working directory
RUN chown -R coder:coder /code

# Run programs as the non-root user
USER coder

CMD ["python", "--version"]