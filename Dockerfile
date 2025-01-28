FROM python:3.10.11

SHELL ["/bin/bash", "-c"]

#USER app
# Set work directory
WORKDIR /code

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
RUN pip install --upgrade pip
ADD ./requirements.txt .
RUN pip install -r requirements.txt

#RUN apt update && apt -qy install libpq-dev


RUN useradd -rms /bin/bash daboggg && chmod 777 /opt /run



RUN mkdir /code/static && mkdir /code/media && mkdir /code/db && chown -R daboggg:daboggg /code && chmod 755 /code

USER daboggg

COPY --chown=daboggg:daboggg . .

#RUN pip install -r requirements.txt


