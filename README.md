# Paperrank


## ⚡️ Highlights
* Semantic search across 19.5M papers using sentence embeddings
* Sub-second query response times using optimized BigQuery vector search
* Transparent similarity scoring - see exactly why papers are recommended
* Simple interface focused on finding relevant research, not feature bloat


---
## 🔑 Overview
This project was largely inspired by the painful process of finding relevant academic papers. While many modern tools rely on increasingly complex reccomendation systems, my experience has been these tools often produce strange and opaque reccomendations. It seemed strange to me that we have built out all these incredible tools, yet we lacked a tool that would allow researchers to expand human knowledge

**The Solution**: Building a platform that provides researchers with simple and fast paper reccomendations based on semantic similarity between paper abstracts. 
 
---


## 🔨 Approach
* **Processed 19.5M academic papers** from the openAlex dataset using an Apache Beam pipeline on Google Cloud Dataflow 
* **Generated semantic embeddings** for paper abstracts using Sentence-Transformers all-MiniLM-L6-v2 model through parallelized Cloud run jobs for efficient processing
* **Implemented Vector Search** using BIGQUERY's Vector Search along with cosine similarity to identify related papers

---- 




Upon embedding the abstracts of all 19.5 million papers, we are able to obtain the most highly relevant papers from our **Bigquery** table via vector search query.
Each of these embeddings are length 384 vectors, this allows **Vector Search** to obtain "similar" papers by finding papers which are closer together in this high dimensional space.


---

## Built With
 * ![Python](https://img.shields.io/badge/Language-Python-blue?style=flat&logo=python&logoColor=green)
* ![Docker](https://img.shields.io/badge/Containerization-Docker-blue?style=flat&logo=docker&logoColor=blue)

* ![Google Cloud](https://img.shields.io/badge/Cloud%20Platform-Google%20Cloud-blue?logo=googlecloud&logoColor=LOGOCOlOR&style=blue)
