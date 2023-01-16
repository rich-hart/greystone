# Install
```
git clone https://github.com/rich-hart/greystone.git
python3 -m venv venv
source ./venv/bin/activate
pip install -r greystone/requirements.txt
```

# Start Program
```
uvicorn greystone.main:app --reload
```
Use API at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

# NOTES
The following endpoints can be used as an anonymous user:
```
	GET /users/
        POST /users/
        GET /users/{user_id}
        POST /users/{user_id}/items/
        POST /users/{user_id}/loans/
        GET /items/
        GET /loans/
```

Must be an authenticated user to use the following endpoints (this demonstrates loan ownership and sharing):
```
	GET /users/me
        GET /loans/{loan_id}
        GET /loans/{loan_id}/schedule
        GET /loans/{loan_id}/summary
        POST /loans/{loan_id}/share
```

# TO DO

* Add unit tests.
* Replace fake token hashing with real encryption for user authentication.
* Further minimize rounding errors.
