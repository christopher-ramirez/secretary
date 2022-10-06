# Secretary tests

You can run tests on your local Python environment with the command :

<pre>
pytest
</pre>

## Docker image

You can also build a docker image dedicated to your tests :

<pre>
docker build -t phe/secretary .
</pre>

Then you can run the tests in a container :

<pre>
docker run -ti \
  -v $PWD:/opt/secretary \
  -e "PYTHONPATH=/opt" \
  -w /opt/secretary \
  phe/secretary pytest -v
</pre>

For special need, you may prefer to run a shell :

<pre>
docker run -ti \
  -v $PWD:/opt/secretary \
  -e "PYTHONPATH=/opt" \
  -w /opt/secretary \
  phe/secretary /bin/bash
</pre>
