PyFuse
========

Python program using Fuse.


Build
-----

    $ docker build . -t py_fuse_image
    $ docker run --rm -d --name py_fuse -v $(pwd):/shared --privileged py_fuse_image
    $ docker exec -ti py_fuse bash

    - Debian:  cf: make_debian_package.sh (source => setuptools => debuild => .deb)



Service / Daemon
----------------
    Debian: 
        * py-fuse (init.d / systemd)    


Executable
----------
    Debian:
        * py-fuse (daemonziable (init.d / systemd))
    

Look how easy it is to use:

    # 


Features
--------

- Fuse


Contribute
----------

- Issue Tracker: 
- Source Code: 

Support
-------

If you are having issues, please let us know.
We have a mailing list located at: benjy80@gmail.com

License
-------

The project is licensed under the <XXX> license.        