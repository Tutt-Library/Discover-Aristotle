# Dockerfile for DigitalCC
FROM tuttlibrary/python-base
MAINTAINER Jeremy Nelson <jermnelson@gmail.com>

# Set environmental variables
ENV DIGCC_GIT https://github.com/Tutt-Library/digital-cc.git
ENV DIGCC_HOME /opt/digital-cc

# Clone master branch of Tutt Library Digitial CC repository,
# setup Python env, run 
RUN git clone $DIGCC_GIT $DIGCC_HOME && \
  cd $DIGCC_HOME && \
  mkdir instance && \
  pip install -r requirements.txt

COPY instance/conf.py $DIGCC_HOME/instance/conf.py
#COPY supervisord.conf /etc/supervisor/conf.d/
EXPOSE 5000

WORKDIR $DIGCC_HOME
#CMD ["/usr/local/bin/supervisord"]
#CMD ["python", "run.py"]
CMD ["nohup", "gunicorn", "-b", "0.0.0.0:5000", "run:app"]
