FROM python:3.11-slim-bookworm
COPY tasks/fracture/case_001/environment/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
ENV PYTHONHASHSEED=0 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/matplotlib
WORKDIR /tmp
USER 65532:65532
