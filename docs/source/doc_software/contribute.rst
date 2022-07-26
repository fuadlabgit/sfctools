Ongoing Development
========================

.. note:: 
  This is an open-source package. Feel free to contribute at any time :)


How to Contribute: General Information 
-------------------------------------
Sfctools is open for your contribution. If you are interested in contributing to the code or the documentation, you are greatfully invited to do so! 
If you want to contribute to this repository, please discuss the changes you wish to make, or new features you want to introduce, with the core development team.
Please also try to adapt your code style in accordance with the coding conventions and quality values of this repository.
Read the Contributors License Agreement (CLA) and send a signed copy to `Thomas Baldauf <mailto:thomas.baldauf@dlr.de>`_.

Release Timeline
----------------

Dated 11/2021.

.. list-table:: Release timeline for past and planned future releases
   :widths: 5,5,5,5
   :header-rows: 1

   * - Planned Quarter
     - Version Number
     - Short Name 
     - (Planned) Features

   * - Q4-2021
     - 0.3 - Alpha release
     - Michelada
     - Core functionalities

   * - Q2-2022*
     - 0.4 - Beta release
     - Chicha 
     - | improved batch functionality and
       | correlation analysis, example projects 

   * - Q4-2022*
     - 0.5 - 
     - Xocolatl
     - | improved statistical testing 
       | (automated steady-state detection),
       | additional example projects


*) Future release

Maintenance Plan 
----------------
The software will be updated in form of bug-fixes and feature extensions. However, the time schedule of future updates is not clearly determined yet. Please be aware that we do not give any warranty about the code provided in the alpha and beta release phases.

Quality Values
-----------------

Dated 11/2021.

.. list-table:: Quality values
   :widths: 35, 35
   :header-rows: 1

   * - Value 
     - Description
   * - Learnability
     - | The highest priority of sfctools is to provide an
       | easy-to-apply tool for scientists (not primarily developers).
       | Hence, easy to understand approaches, code structures 
       | and explicit formulations are favored.
   * - Readability
     - | The readability of the code is a key aspect.
       | Splitting of statements is favored over convoluted one-liners.
   * - Reliability
     - | The provided tools should be reliable 
       | and stable (if not, a beta release warning is added).
   * - Performance
     - | Agent-based simulation tools are anyways slower
       | than other modeling approaches. Therefore, performance
       | should only be optimized where necessary.

Coding Conventions
----------------------------

Dated 11/2021.

- mainly PEP-8 coding style https://www.python.org/dev/peps/pep-0008/
- exception are economic and mathematical variables that have capital letters for convenience 


Why Python?
-------------

Python is the ’programming language of engineers’ and follows the philosophy of open source. It opens the
world of programming to engineers and non-programming specialists via an easy installation and import of
modules, shipping powerful toolboxes in an easy-to-read syntax. The aim of providing this framework in Python
is to lower the entry barrier for economists and engineers to macroeconomic computer modeling, and, at the
same time, to allow for the design of highly flexible, custom-built simulations.


Organizational Information 
--------------------------

Core Development Team 
^^^^^^^^^^^^^^^^^^^^^^

The core development team of sfctools is listed in the table below (dated 11/2021).

.. list-table:: 
   :widths: 35, 35
   :header-rows: 1

   * - Role
     - Responsible
   * - Scrum Master
     - Benjamin Fuchs [#f1]_ 
   * - Developer 
     - Thomas Baldauf [#f2]_
   * - Product Owner 
     - | M. O`Sullivan [#f2]_ 


.. [#f1]  Department of Energy System Analysis at Institute of Networked Energy Systems, DLR 
.. [#f2]  Energy Economics Group, Department of Energy System Analysis at Institute of Networked Energy Systems, DLR 

Open-Source Readiness 
^^^^^^^^^^^^^^^^^^^^^
| Features, dependencies and components which are contraindicative or at odds
| with an open source publication should not be part of this package.