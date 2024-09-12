from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
import subprocess
import uuid
from execution import execute_script

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///schedulers.db'

db = SQLAlchemy(app)

scheduler = BackgroundScheduler()
scheduler.add_jobstore('sqlalchemy', url='sqlite:///jobs.db')
scheduler.start()

class Execution(db.Model):
    code = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cron_expression = db.Column(db.String(100), nullable=False)
    script_content = db.Column(db.Text, nullable=False)
    dependencies = db.Column(db.Text, nullable=True)

def parse_cron(cron_expression):
    cron_parts = cron_expression.split()

    return {
        'minute': cron_parts[0],
        'hour': cron_parts[1],
        'day': cron_parts[2],
        'month': cron_parts[3],
        'day_of_week': cron_parts[4],
    }

def schedule_execution(execution_code, cron_expression, script_content, dependencies):
    scheduler.add_job(
        func='execution.execute_script', 
        trigger='cron', 
        id=execution_code, 
        args=[script_content, dependencies], 
        **parse_cron(cron_expression)
    )

@app.route('/schedule', methods=['POST'])
def schedule_execution():
    try:
        data = request.get_json()
        
        name = data['name']
        cron_expression = data['cron_expression']
        script_content = data['script_content']
        dependencies = data.get('dependencies', None)

        code = str(uuid.uuid4()) 

        new_execution = Execution(
            code=code, 
            name=name, 
            cron_expression=cron_expression, 
            script_content=script_content, 
            dependencies=dependencies
        )

        db.session.add(new_execution)
        db.session.commit()

        schedule_execution(code, cron_expression, script_content, dependencies)

        return jsonify({"message": "Execução adicionada com sucesso!", "code": code}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
@app.route('/schedule/<code>', methods=['DELETE'])
def unschedule_execution(code):
    try:
        job = scheduler.get_job(code)
        if job:
            scheduler.remove_job(code)

        execution = Execution.query.filter_by(code=code).first()
        if execution:
            db.session.delete(execution)
            db.session.commit()

        return jsonify({"message": "Execução removida com sucesso!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
