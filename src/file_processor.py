from unstructured.partition.pdf import partition_pdf


def process_file(file_path):
    file_type =file_path.split('.')[-1]
    if file_type.lower()=='pdf':
        process_pdf(file_path)




def process_pdf(file):
    elements = partition_pdf( filename=file)
    print(elements)