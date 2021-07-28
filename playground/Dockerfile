FROM jupyter/base-notebook

# Make src directory to contain necessary items
RUN mkdir analysis
WORKDIR /analysis
COPY . .

# Install requirements
RUN pip3 install -r requirements.txt \
    && python3 -m spacy download en_core_web_md
RUN jupyter notebook --NotebookApp.iopub_data_rate_limit=1.0e10
