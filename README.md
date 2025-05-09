# LDAPLynx
LDAPLynx is a tool used to explore LDIFs for Red Teamers.

![LDAPLynx Logo](https://github.com/Toad24/LDAPLynx/raw/main/assets/logo.png)

## Features
- Load and parse LDIF files.
- Visualize LDAP nodes and relationships.
- Export relationships to Gephi.

## Getting Started

Clone the repository:

```bash
git clone https://github.com/your-username/ldaplynx.git
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the tool:

```bash
python ldaplynx.py
```


## Usage

This tool is intended to allow an operator to export an OpenLDAP database as an LDIF, create node/edge relationships from that LDIF, and then view those relationships in Gephi.

![LDAPLynx Console](https://github.com/Toad24/LDAPLynx/raw/main/assets/use.png)


![Gephi Use](https://github.com/Toad24/LDAPLynx/raw/main/assets/gephi.png)