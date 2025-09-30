# Paperrank

## Providing powerful research paper reccomendations through similarity search among research paper's abstracts

A large part of research involves the ability to find relevant papers to topics, which are often quite niche making this task hard at times. Many models
propose extremely complex and bloated reccomendation models for research papers. Paperrank seeks to provide researchers with a very simplistic reccomendation
model, similarity search among abstracts. When an abstract is written well, it effectively tells you the entire story of a research paper, thus we are able
to obtain highly relevant papers by simply comparing abstracts.

---

Upon embedding the abstracts of all 19.5 million papers, we are able to obtain the most highly relevant papers from our **Bigquery** table via vector search query.
Each of these embeddings are length 384 vectors, this allows **Vector Search** to obtain "similar" papers by finding papers which are closer together in this high dimensional space.


---

## Built With
![Python](https://img.shields.io/badge/Language-Python-blue?style=flat&logo=python&logoColor=green)
![Docker](https://img.shields.io/badge/Containerization-Docker-blue?style=flat&logo=docker&logoColor=blue)

![Google Cloud](https://img.shields.io/badge/Cloud%20Platform-Google%20Cloud-blue?logo=googlecloud&logoColor=LOGOCOlOR&style=blue)