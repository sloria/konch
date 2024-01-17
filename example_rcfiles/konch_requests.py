# vi: set ft=python :
import requests

import konch

konch.config(
    {
        "context": [requests.get, requests.post, requests.put, requests.delete],
        "banner": "A humanistic HTTP shell",
    }
)
