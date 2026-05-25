import nltk

resources = [
    "punkt",
    "punkt_tab",
    "averaged_perceptron_tagger",
    "wordnet",
    "omw-1.4"
]

for resource in resources:
    nltk.download(resource)