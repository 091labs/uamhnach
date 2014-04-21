# Uamhnach

Uamhnach is the Gaelic for 'awesome'.

## What's this?

This will be the way 091 labs handles member data (it's not yet). This will
eventually include:

* Membership info (name, email, shoe size etc.)
* Membership fees
* Credit for the tuck shop and print server
* Inventory of items and stock in the labs
* Booking of hot desks
* Events happening at the labs
* Oauth provision (get your oauth from us)
* Oauth linking (sign up/sign in with your favourite oauth provider)

## Installation

First, install the packages listed in requirements.txt
`pip install -r requirements.txt`

Then cp the sample config
`cp sample_config.py config.py`

Edit the config to point at your database then run `./db_create.py`

Now you should be able to just do `./run.py`
