# -*- coding: utf-8 -*-
"""
Created on 14.07.2011

@author: Sebastian Wallat
"""

if __name__ == '__main__':
    import dissomniag
    data1 = """
{
  "Herausgeber": "Xema",
  "Nummer": "1234-5678-9012-3456",
  "Deckung": 2e+6,
  "Währung": "EUR",
  "Inhaber": {
    "Name": "Mustermann",
    "Vorname": "Max",
    "männlich": true,
    "Depot": {},
    "Hobbys": [ "Reiten", "Golfen", "Lesen" ],
    "Alter": 42,
    "Kinder": [],
    "Partner": null
  }
}"""    
    dissomniagcli.rpcClient(data1)