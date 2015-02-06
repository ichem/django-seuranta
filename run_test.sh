#! /usr/bin/env bash
coverage run --source=seuranta manage.py test
coverage report
