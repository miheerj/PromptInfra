#!/usr/bin/env python3
"""
Simple FinOps Dashboard Generator
Creates QuickSight dashboard for cost tracking
"""

import json
from pathlib import Path
from datetime import datetime, timedelta

# Optional AWS integration
try:
    import boto3
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

class FinOpsDashboard:
    def __init__(self):
        self.tracking_dir = Path("finops_tracking")
        
    def get_all_deployments(self):
        """Get all deployment tracking files"""
        deployments = []
        
        if self.tracking_dir.exists():
            for tracking_file in self.tracking_dir.glob("*.json"):
                try:
                    with open(tracking_file, 'r') as f:
                        deployment = json.load(f)
                        deployments.append(deployment)
                except Exception as e:
                    print(f"Error reading {tracking_file}: {e}")
        
        return deployments
    
    def generate_cost_summary_csv(self):
        """Generate CSV for QuickSight import"""
        deployments = self.get_all_deployments()
        
        csv_content = "deployment_id,created_at,prompt,resource_count,estimated_monthly_cost,cost_center,created_by\\n"
        
        for deployment in deployments:
            csv_content += f"{deployment['deployment_id']},"
            csv_content += f"{deployment['created_at']},"
            csv_content += f"\\\"{deployment['prompt']}\\\"," 
            csv_content += f"{deployment['resource_count']},"
            csv_content += f"{deployment['estimated_monthly_cost']},"
            csv_content += f"{deployment['tags']['cost_center']},"
            csv_content += f"{deployment['tags']['created_by']}\\n"
        
        # Save CSV
        csv_file = Path("finops_dashboard_data.csv")
        csv_file.write_text(csv_content)
        
        print(f"✅ Generated cost summary CSV: {csv_file}")
        return csv_file
    
    def generate_quicksight_setup_script(self):
        """Generate AWS CLI commands to set up QuickSight dashboard"""
        
        setup_script = f'''#!/bin/bash
# QuickSight Dashboard Setup for FinOps Tracking
# Run this script to create a basic cost tracking dashboard

echo "🏗️  Setting up FinOps QuickSight Dashboard..."

# 1. Upload CSV to S3 (replace YOUR_BUCKET with your S3 bucket)
aws s3 cp finops_dashboard_data.csv s3://YOUR_BUCKET/finops/data/

# 2. Create QuickSight DataSource (you may need to adjust account ID and region)
aws quicksight create-data-source \\
  --aws-account-id $(aws sts get-caller-identity --query Account --output text) \\
  --data-source-id "finops-terraform-data" \\
  --name "FinOps Terraform Tracking" \\
  --type "S3" \\
  --data-source-parameters S3Parameters="{{ManifestFileLocation={{Bucket=YOUR_BUCKET,Key=finops/data/finops_dashboard_data.csv}}}}" \\
  --permissions "{{Principal=$(aws sts get-caller-identity --query Arn --output text),Actions=[quicksight:DescribeDataSource,quicksight:DescribeDataSourcePermissions,quicksight:PassDataSource]}}"

# 3. Create DataSet
aws quicksight create-data-set \\
  --aws-account-id $(aws sts get-caller-identity --query Account --output text) \\
  --data-set-id "finops-terraform-dataset" \\
  --name "FinOps Terraform Dataset" \\
  --physical-table-map '{{"finops-table":{{"S3Source":{{"DataSourceArn":"arn:aws:quicksight:us-east-1:$(aws sts get-caller-identity --query Account --output text):datasource/finops-terraform-data","InputColumns":[{{"Name":"deployment_id","Type":"STRING"}},{{"Name":"created_at","Type":"DATETIME"}},{{"Name":"prompt","Type":"STRING"}},{{"Name":"resource_count","Type":"INTEGER"}},{{"Name":"estimated_monthly_cost","Type":"DECIMAL"}},{{"Name":"cost_center","Type":"STRING"}},{{"Name":"created_by","Type":"STRING"}}]}}}}}}' \\
  --permissions "{{Principal=$(aws sts get-caller-identity --query Arn --output text),Actions=[quicksight:DescribeDataSet,quicksight:DescribeDataSetPermissions,quicksight:PassDataSet,quicksight:DescribeIngestion,quicksight:ListIngestions]}}"

echo "✅ Basic setup complete!"
echo "📊 Next steps:"
echo "   1. Go to AWS QuickSight console"
echo "   2. Create a new analysis using the 'FinOps Terraform Dataset'"
echo "   3. Add visualizations for:"
echo "      - Total estimated costs by deployment"
echo "      - Resource count over time"  
echo "      - Cost by cost center"
echo "      - Monthly trend analysis"
'''
        
        script_file = Path("setup_quicksight.sh")
        script_file.write_text(setup_script)
        script_file.chmod(0o755)  # Make executable
        
        print(f"✅ Generated QuickSight setup script: {script_file}")
        return script_file
    
    def generate_simple_html_dashboard(self):
        """Generate a simple HTML dashboard as an alternative to QuickSight"""
        deployments = self.get_all_deployments()
        
        # Calculate totals
        total_cost = sum(d['estimated_monthly_cost'] for d in deployments)
        total_resources = sum(d['resource_count'] for d in deployments)
        
        html_content = f'''<!DOCTYPE html>
<html>
<head>
    <title>FinOps Terraform Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: #232f3e; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .stats {{ display: flex; gap: 20px; margin-bottom: 20px; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 8px; flex: 1; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #232f3e; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        table {{ width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #232f3e; color: white; }}
        .cost {{ color: #d13212; font-weight: bold; }}
        .deployment-id {{ font-family: monospace; background: #f8f9fa; padding: 2px 6px; border-radius: 3px; }}
        .alert {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 4px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏦 FinOps Terraform Dashboard</h1>
            <p>Cost tracking for AI-generated infrastructure</p>
            <p><small>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{len(deployments)}</div>
                <div class="stat-label">Total Deployments</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${total_cost:.2f}</div>
                <div class="stat-label">Estimated Monthly Cost</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_resources}</div>
                <div class="stat-label">Total Resources</div>
            </div>
        </div>
        
        {f'<div class="alert">⚠️ High cost alert: Monthly estimate exceeds $100</div>' if total_cost > 100 else ''}
        
        <table>
            <thead>
                <tr>
                    <th>Deployment ID</th>
                    <th>Created</th>
                    <th>Resources</th>
                    <th>Est. Monthly Cost</th>
                    <th>Prompt</th>
                </tr>
            </thead>
            <tbody>'''
        
        # Sort by creation date (newest first)
        deployments.sort(key=lambda x: x['created_at'], reverse=True)
        
        for deployment in deployments:
            created_date = datetime.fromisoformat(deployment['created_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d')
            prompt_short = deployment['prompt'][:80] + ('...' if len(deployment['prompt']) > 80 else '')
            
            html_content += f'''
                <tr>
                    <td><span class="deployment-id">{deployment['deployment_id']}</span></td>
                    <td>{created_date}</td>
                    <td>{deployment['resource_count']}</td>
                    <td class="cost">${deployment['estimated_monthly_cost']:.2f}</td>
                    <td>{prompt_short}</td>
                </tr>'''
        
        html_content += '''
            </tbody>
        </table>
        
        <div style="margin-top: 30px; padding: 20px; background: white; border-radius: 8px;">
            <h3>📊 Next Steps for Advanced Analytics</h3>
            <ul>
                <li><strong>AWS QuickSight:</strong> Run <code>./setup_quicksight.sh</code> for advanced dashboards</li>
                <li><strong>Cost Explorer:</strong> Filter by tag <code>created_by:terraform-generator</code></li>
                <li><strong>CloudWatch:</strong> Set up cost anomaly detection</li>
                <li><strong>Weekly Reports:</strong> Lambda functions will send cost alerts</li>
            </ul>
        </div>
    </div>
</body>
</html>'''
        
        dashboard_file = Path("finops_dashboard.html")
        dashboard_file.write_text(html_content, encoding='utf-8')
        
        print(f"✅ Generated HTML dashboard: {dashboard_file}")
        print(f"🌐 Open in browser: file://{dashboard_file.absolute()}")
        return dashboard_file
    
    def generate_cost_report(self):
        """Generate a simple cost report"""
        deployments = self.get_all_deployments()
        
        if not deployments:
            print("📊 No deployments found for cost reporting")
            return
        
        print("\\n" + "="*60)
        print("💰 FINOPS COST REPORT")
        print("="*60)
        
        total_cost = 0
        for deployment in deployments:
            cost = deployment['estimated_monthly_cost']
            total_cost += cost
            
            print(f"🆔 {deployment['deployment_id']}")
            print(f"   📅 Created: {deployment['created_at'][:10]}")
            print(f"   💳 Est. Cost: ${cost:.2f}/month")
            print(f"   📦 Resources: {deployment['resource_count']}")
            print(f"   📝 Prompt: {deployment['prompt'][:60]}...")
            print()
        
        print(f"💰 TOTAL ESTIMATED MONTHLY COST: ${total_cost:.2f}")
        
        if total_cost > 100:
            print("⚠️  WARNING: High monthly cost detected!")
        
        print("="*60)

def main():
    """Generate FinOps dashboard and reports"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate FinOps dashboard for Terraform deployments")
    parser.add_argument("--format", choices=['html', 'csv', 'quicksight', 'report'], 
                       default='html', help="Output format")
    
    args = parser.parse_args()
    
    dashboard = FinOpsDashboard()
    
    if args.format == 'html':
        dashboard.generate_simple_html_dashboard()
    elif args.format == 'csv':
        dashboard.generate_cost_summary_csv()
    elif args.format == 'quicksight':
        dashboard.generate_cost_summary_csv()
        dashboard.generate_quicksight_setup_script()
    elif args.format == 'report':
        dashboard.generate_cost_report()
    
    print("\\n✅ FinOps dashboard generation complete!")

if __name__ == "__main__":
    main()
