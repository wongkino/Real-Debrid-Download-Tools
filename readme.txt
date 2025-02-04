
docker build -t real-debrid-web-batch .
docker run -d -p 5000:5000 real-debrid-web-batch
打開瀏覽器訪問 http://localhost:5000
