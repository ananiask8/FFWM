python setup.py install
python setup.py sdist bdist_wheel

cd ./cuda/block_extractor
python setup.py install
python setup.py sdist bdist_wheel

cd ../local_attn_reshape
python setup.py install
python setup.py sdist bdist_wheel

cd ../resample2d_package
python setup.py install
python setup.py sdist bdist_wheel
