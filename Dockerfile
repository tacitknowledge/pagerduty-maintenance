FROM jenkinsci/jnlp-slave:3.19-1

USER root
ADD requirements.txt /root/requirements.txt
ADD maintenance_window.py /bin/maintenance_window.py
RUN apt-get update -y \
	&& apt-get install python-pip -y \
	&& pip install -r /root/requirements.txt \
	&& chmod +x /bin/maintenance_window.py
