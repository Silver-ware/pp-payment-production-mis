from django import template
import requests

register = template.Library()

# Tag to fetch data from a URL
@register.simple_tag
def fetch_data(url, var_name=None):
    """Fetch data from a URL and return it, storing the result in a variable."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json() if response.headers['Content-Type'] == 'application/json' else response.text
        if var_name:
            return f"{var_name} = {data}"
        return data
    except requests.exceptions.RequestException as e:
        return f"<!-- Error fetching data from {url}: {e} -->"
