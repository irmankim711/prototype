from celery import shared_task
from .services.report_service import report_service
from .services.ai_service import get_ai_service
from .models import Report, db

@shared_task
def generate_report_task(user_id, data):
    try:
        # Get AI suggestions for the report
        suggestions = get_ai_service().generate_report_suggestions(data)
        
        # Merge suggestions with user data
        enriched_data = {**data, 'ai_suggestions': suggestions}
        
        # Generate the report
        output_path = report_service.generate_report(
            template_id=data.get('template_id'),
            data=enriched_data
        )
        
        # Update report status in database
        report = Report.query.get(data.get('report_id'))
        if report:
            report.status = 'completed'
            report.output_url = output_path
            db.session.commit()
        
        return {
            'status': 'success',
            'output_path': output_path,
            'suggestions': suggestions
        }
        
    except Exception as e:
        # Update report status to failed
        report = Report.query.get(data.get('report_id'))
        if report:
            report.status = 'failed'
            db.session.commit()
            
        return {
            'status': 'error',
            'error': str(e)
        }
