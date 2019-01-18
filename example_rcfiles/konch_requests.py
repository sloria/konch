# vi: set ft=python :
import konch
import requests

konch.config(
    {
        "context": [requests.get, requests.post, requests.put, requests.delete],
        "banner": "A humanistic HTTP shell",
    }
)
