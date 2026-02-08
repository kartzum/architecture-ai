## Создание векторного индекса базы знаний

### Как создать индекс?

**Создание образа**

```
docker build -t text-indexer .
```

**Запуск**

```
docker run --rm \
  -v $(pwd)/my_texts:/app/text_files \
  -v $(pwd)/faiss_index:/app/faiss_index \
  text-indexer
```


