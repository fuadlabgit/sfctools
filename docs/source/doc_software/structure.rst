Framework Structure 
======================

Sfctools is designed in a relatively flat architecture. It combines different sub-modules.
The features can be categorized into data structures for agents, bottom-up modeling tools and managerial (parameters and data-related) features.


.. |img1| image::  redblock.png
   :width: 80pt
   :height: 80pt
  
.. |img2| image::  greenblock.png
   :width: 80pt
   :height: 120pt
  

.. |img3| image::  blueblock.png
   :width: 80pt
   :height: 120pt
  
  


===========================  ======================== =====================
*Automation and Parameters*   *Bottom-Up Tools*        *Data Structures*   
===========================  ======================== =====================
|img1|   4 Submodules         |img2|  6 Submodules      |img3|    6 Submodules      


Yaml hyperparameters          Flow matrix              Income statement 
Clock                         World (registry)         Cashflow statement
Stock manager                 Balance sheet            Inventory 
Model runner                  Market registry          Worker registry
_                             Decentralized matching   Bank order book
_                             Production tree          Signals and slots 
                                                       
===========================  ======================== =====================

More information can be found in the module handbook.