from threading import Thread
from flask import Blueprint, jsonify, render_template, request
import PyPDF2
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import PyPDF2
import pandas as pd
import os

documents = Blueprint('documents', __name__)




