
from app import db
from app.models.task import Task
from app.models.goal import Goal
from flask import request, Blueprint, make_response, jsonify
from sqlalchemy import asc, desc
from datetime import datetime
import os 
import requests

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")
goals_bp = Blueprint('goals', __name__, url_prefix='/goals')

def is_complete(completed_at):
  
    if completed_at is None:
        return False
    else:
        return True
token=os.environ.get('SLACK_TOKEN')

@tasks_bp.route("", methods=["GET", "POST"])
def handle_tasks():

    if request.method == "GET":
        tasks = Task.query.all()
        title_query = request.args.get("sort")
        if title_query == "asc":
            tasks = Task.query.order_by(asc(Task.title))
        elif title_query == "desc":
            tasks = Task.query.order_by(desc(Task.title))

        tasks_response = []
        
        for task in tasks:
            if task.completed_at is None :
                 tasks_response.append({
                "id": task.task_id,
                "title": task.title,
                "description": task.description,
                "is_complete" : False
            })
            else:
                tasks_response.append({
                    "id": task.task_id,
                    "title": task.title,
                    "description": task.description,
                    "completed_at": task.completed_at,
                    "is_complete" : False
                })
        return jsonify(tasks_response), 200
      
    if request.method == "POST": 
        request_body = request.get_json()
        if "title" not in request_body or "description" not in request_body or "completed_at" not in request_body:
            return make_response({
                "details": "Invalid data"
                }, 400)
        else:
            new_task = Task(title=request_body["title"], description=request_body["description"], completed_at=request_body["completed_at"])
            db.session.add(new_task)
            db.session.commit()
            return make_response(
                    { "task": {
                    "id": new_task.task_id,
                    "title": new_task.title,
                    "description": new_task.description,
                    "is_complete": is_complete(new_task.completed_at)
                    }}, 201)

@tasks_bp.route("/<task_id>", methods=["GET","PUT", "DELETE"])
def handle_tasks_id(task_id):
    task = Task.query.get(task_id)
    if task is None:
            return make_response("", 404)

    if request.method == "GET":
        if task is not None:
            return {"task":{
                    "id": task.task_id,
                    "title": task.title,
                    "description": task.description,
                    "is_complete": False    
        }}
    
    
    elif request.method == "PUT":
        data = request.get_json()
        
        task.title = data["title"]
        task.description = data["description"]
        task.completed_at = data["completed_at"]

        db.session.commit()
        
        data_response= {
        "task": {
            "id": task.task_id,
            "title": task.title,
            "description": task.description,
            "is_complete": is_complete(task.completed_at)
        }
    }
        return make_response(jsonify(data_response),200)
   

    elif request.method == "DELETE":
        db.session.delete(task)
        db.session.commit()
        
        delete_id_response= f'Task {task.task_id} "{task.title}" successfully deleted'
        
        return make_response(jsonify({"details":delete_id_response}))


@tasks_bp.route("/<task_id>/mark_complete", methods = ["PATCH"])
def handle_complete(task_id):
    task = Task.query.get(task_id)
    
    if task is None :
        return make_response("", 404)

    task.completed_at = datetime.now()

    db.session.commit()
    
    slack_url='https://slack.com/api/chat.postMessage'
    token= os.environ.get("SLACK_TOKEN")
    params = {
        'channel': 'task-notifications',
        'text': f'Someone just completed the task {task.title}'
    }
    headers={
        'Content-type': 'application/json',
        'Authorization': f"Bearer {token}"
    }

    requests.post(slack_url,json=params,headers=headers)
    data_response = {
        "task": {
            "id": task.task_id,
            "title": task.title,
            "description": task.description,
            "is_complete": True 
        }
    }


    return make_response(jsonify(data_response),200)
  


@tasks_bp.route("/<task_id>/mark_incomplete", methods = ["PATCH"])
def handle_incomplete(task_id):
    task = Task.query.get(task_id)

    if task is None:
        return make_response("",404)
    
    data_response = {
        "task": {
            "id": task.task_id,
            "title": task.title,
            "description": task.description,
            "is_complete": False
        }
    }
    db.session.commit()
    if task.completed_at is None : 
        return make_response(jsonify(data_response),200)
    
    task.completed_at = None
    return make_response(jsonify(data_response),200)




# Routes for Goal

@goals_bp.route("", methods=["GET","POST"])
def handle_goals():
    goal_reponse=[]
    goals = Goal.query.all()
  
    if request.method == "GET":
    
        for goal in goals:
            
            goal_reponse.append({
                "id": goal.goal_id,
                "title":goal.title,
            })
        return make_response(jsonify(goal_reponse),200)

    else:
        request_body = request.get_json()
        if "title" not in request_body:
            return make_response({"details": "Invalid data"}, 400)    
        new_goal = Goal(title = request_body["title"])
        db.session.add(new_goal)
        db.session.commit()
        response_data = {
        "goal": {
            'id': new_goal.goal_id,
            "title":new_goal.title

        }
    
    } 

        return make_response(response_data,201)

 



@goals_bp.route("/<goal_id>", methods= ["GET","PUT","DELETE"])
def handle_goal_id(goal_id):
    goal = Goal.query.get(goal_id)
    if goal is None:
        return make_response("",404)
    if request.method == "GET":
        if goal is not None:
            return {
                "goal":{
                    "id" : goal.goal_id,
                    "title": goal.title
                }
            }
    
    elif request.method == "PUT":
        data = request.get_json()
        goal.title= data["title"]
        db.session.commit()

        data_response= {
            "goal":{
                "id": goal.goal_id,
                "title": goal.title
            }
        }

        return make_response(data_response)

    elif request.method == "DELETE":
        db.session.delete(goal)
        db.session.commit()
        delete_id_response= f'Goal {goal_id} "{goal.title}" successfully deleted'
        return make_response(jsonify({"details":delete_id_response}))

# @goals_bp.route('<goal_id>/tasks', methods=["GET", "POST"])

    
