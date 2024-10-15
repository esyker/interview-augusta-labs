# Interview Augusta Labs

## Preview

https://github.com/user-attachments/assets/8b0de958-c27c-4032-a350-b63aa7bd1c81

## Requirements

`requirements.txt` was created using:

 ```shell
 pip list --format=freeze > requirements.txt
 ```
 and can be used to install the requirements to a pip enviroment using:
```shell
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

## Running

To run the backend:
```shell
cd src/backend
python main.py
```

To run the frontend:
```shell
cd src/frontend
npm install
npm start
```

## Requests

Some sample requests:

- List the last pt articles:
```shell
http://127.0.0.1:8000/wikipedia/list_last_pt_articles?total_limit=5
```

- Get the parsed last pt articles:
```shell
http://127.0.0.1:8000/wikipedia/get_last_pt_articles?total_limit=5&requests_per_second=2&processing_type=fast&verbose=true
```

- Get the results for a user query:

```shell
http://127.0.0.1:8000/user/query_results?query=Hist%C3%B3ria&top_k=10&scrapping_total_limit=50&reuse_index=False
```

OR for reusing the index:

```shell
http://127.0.0.1:8000/user/query_results?query=Machine%20Learning&top_k=5&scrapping_total_limit=10&reuse_index=True
``` 

- Get refined search:
```shell
http://127.0.0.1:8000/user/query_refined?top_k=5&positive=Museo_Travesti_del_Per%C3%BA&negative=Estudos_transg%C3%AAnero&negative=One_of_Ours
```
