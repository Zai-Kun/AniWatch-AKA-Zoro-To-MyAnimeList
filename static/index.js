// Yes, most of the JS was written by ChatGPT since I'm not proficient in JS.💀

let response;

function send(token_req) {
  token = prompt('Enter your refresh token');
  if (token != null && token != '') {
    const data = {};
    data[token_req] = token;
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/token');
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = () => {
      if (xhr.status === 200) {
        response = JSON.parse(xhr.responseText);
        if ('html' in response) {
          document.write(response["html"]);
        }
        else{
          alert(response["text"])
        }
      }
      else {
        console.error('Request failed.');
      }
    };
    xhr.send(JSON.stringify(data));
  }
}

function copy(token) {
  text = response[token]
  navigator.clipboard.writeText(text)
    .then(() => {
      alert('Copied to clipboard');
    })
    .catch((err) => {
      alert(`Error copying to clipboard: ${err}`);
    });
}

