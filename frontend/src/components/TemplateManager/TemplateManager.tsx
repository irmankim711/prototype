import React, { useState, useEffect } from 'react';
import { Box, Typography, Card, CardContent, Grid, Button, Chip, IconButton, Tooltip, Tabs, Tab } from '@mui/material';
import { Edit, Delete, Download, Visibility, Add, Upload, Settings } from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import TemplateEditor from './TemplateEditor';
import TemplateViewer from './TemplateViewer';
import TemplateImportExport from './TemplateImportExport';
import TemplateService from '../../services/templateService';

interface Template {
  id: string;
  name: string;
  type: 'latex' | 'jinja2' | 'docx';
  description: string;
  content: string;
  createdAt: string;
  updatedAt: string;
}

const TemplateManager: React.FC = () => {
  const theme = useTheme();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [showEditor, setShowEditor] = useState(false);
  const [showViewer, setShowViewer] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null);
  const [activeTab, setActiveTab] = useState(0);

  useEffect(() => {
    // Load templates from local storage or API
    loadTemplates();
  }, []);

  const loadTemplates = () => {
    // Load templates from the service
    const storedTemplates = TemplateService.getTemplates();
    const defaultTemplates: Template[] = [
      {
        id: '1',
        name: 'LaTeX Report Template',
        type: 'latex',
        description: 'Comprehensive LaTeX template for program reports with evaluation tables',
        content: `% Setting up the document class and basic configurations
\\documentclass[a4paper,12pt]{article}
\\usepackage[utf8]{inputenc}
\\usepackage[T1]{fontenc}
\\usepackage{geometry}
\\geometry{margin=1in}
\\usepackage{booktabs}
\\usepackage{graphicx}
\\usepackage{longtable}
\\usepackage{colortbl}
\\usepackage{xcolor}
\\usepackage{enumitem}
\\usepackage{amsmath}
\\usepackage{pdflscape}
\\usepackage{noto}

% Defining colors for tables
\\definecolor{lightgray}{gray}{0.9}

% Document begins
\\begin{document}

% Title Page
\\begin{center}
    \\vspace*{1cm}
    \\textbf{\\huge LAPORAN {{program.title}}}\\\\
    \\vspace{0.5cm}
    \\textbf{{{program.location}}}\\\\
    \\vspace{0.5cm}
    \\textbf{Tarikh: {{program.date}}}\\\\
    \\vspace{0.5cm}
    \\textbf{Masa: {{program.time}}}\\\\
    \\vspace{1cm}
    \\textbf{ANJURAN: {{program.organizer}}}\\\\
    \\vspace{0.5cm}
    \\textbf{PERUNDING: MUBARAK RESOURCES}
\\end{center}

% Table of Contents
\\tableofcontents
\\newpage

% Section 1: Program Information
\\section{Maklumat Program}
\\begin{tabular}{|l|l|}
    \\hline
    \\textbf{Latar Belakang Kursus} & {{program.background}} \\\\
    \\hline
    \\textbf{Tarikh} & {{program.date}} \\\\
    \\hline
    \\textbf{Tempat} & {{program.place}} \\\\
    \\hline
    \\textbf{Penceramah} & {{program.speaker}} \\\\
    \\hline
    \\textbf{Jurulatih} & {{program.trainer}} \\\\
    \\hline
    \\textbf{Fasilitator} & {{program.facilitator}} \\\\
    \\hline
    \\textbf{Jumlah Peserta (Lelaki)} & {{program.male_participants}} \\\\
    \\hline
    \\textbf{Jumlah Peserta (Perempuan)} & {{program.female_participants}} \\\\
    \\hline
    \\textbf{Jumlah Keseluruhan Hadir} & {{program.total_participants}} \\\\
    \\hline
    \\textbf{Urusetia} & {{program.secretariat}} \\\\
    \\hline
    \\textbf{Syarikat Pengangkutan} & {{program.transport_company}} \\\\
    \\hline
    \\textbf{Katering} & {{program.catering}} \\\\
    \\hline
\\end{tabular}

% Section 2: Course Objectives
\\section{Objektif Kursus}
Setelah mengikuti modul, peserta akan:
\\begin{itemize}
    \\item {{program.objectives if program.objectives else 'PROGRAM OBJECTIVES'}}
\\end{itemize}

% Section 3: Program Tentative
\\section{Tentatif Program}
\\subsection{Hari Pertama ({{program.day1_date}})}
\\begin{longtable}{|p{2cm}|p{3cm}|p{7cm}|p{3cm}|}
    \\hline
    \\rowcolor{lightgray}
    \\textbf{Masa} & \\textbf{Perkara/Aktiviti} & \\textbf{Penerangan} & \\textbf{Pengendali Slot} \\\\
    \\hline
    \\endhead
    {% for tentative in tentative.day1 %}
    {{tentative.time}} & {{tentative.activity}} & {{tentative.description}} & {{tentative.handler}} \\\\
    \\hline
    {% endfor %}
\\end{longtable}

\\subsection{Hari Kedua ({{program.day2_date}})}
\\begin{longtable}{|p{2cm}|p{3cm}|p{7cm}|p{3cm}|}
    \\hline
    \\rowcolor{lightgray}
    \\textbf{Masa} & \\textbf{Perkara/Aktiviti} & \\textbf{Penerangan} & \\textbf{Pengendali Slot} \\\\
    \\hline
    \\endhead
    {% for tentative in tentative.day2 %}
    {{tentative.time}} & {{tentative.activity}} & {{tentative.description}} & {{tentative.handler}} \\\\
    \\hline
    {% endfor %}
\\end{longtable}

% Section 4: Program Evaluation
\\section{Penilaian Program}
\\begin{tabular}{|c|p{6cm}|c|c|c|c|c|}
    \\hline
    \\rowcolor{lightgray}
    \\textbf{Jenis Penilaian} & \\textbf{Skala} & \\textbf{1} & \\textbf{2} & \\textbf{3} & \\textbf{4} & \\textbf{5} \\\\
    \\hline
    \\multicolumn{7}{|c|}{\\textbf{A – Kandungan Kursus}} \\\\
    \\hline
    Menepati objektif kursus & Jumlah Penilaian & {{evaluation.content.objective.1}} & {{evaluation.content.objective.2}} & {{evaluation.content.objective.3}} & {{evaluation.content.objective.4}} & {{evaluation.content.objective.5}} \\\\
    \\hline
    Kandungan modul memberi impak & Jumlah Penilaian & {{evaluation.content.impact.1}} & {{evaluation.content.impact.2}} & {{evaluation.content.impact.3}} & {{evaluation.content.impact.4}} & {{evaluation.content.impact.5}} \\\\
    \\hline
    Jangka masa sesi & Jumlah Penilaian & {{evaluation.content.duration.1}} & {{evaluation.content.duration.2}} & {{evaluation.content.duration.3}} & {{evaluation.content.duration.4}} & {{evaluation.content.duration.5}} \\\\
    \\hline
    \\multicolumn{7}{|c|}{\\textbf{B – Alat Bantu Mengajar}} \\\\
    \\hline
    Cetakkan nota & Jumlah Penilaian & {{evaluation.tools.notes.1}} & {{evaluation.tools.notes.2}} & {{evaluation.tools.notes.3}} & {{evaluation.tools.notes.4}} & {{evaluation.tools.notes.5}} \\\\
    \\hline
    Nota mudah fahami & Jumlah Penilaian & {{evaluation.tools.notes_clarity.1}} & {{evaluation.tools.notes_clarity.2}} & {{evaluation.tools.notes_clarity.3}} & {{evaluation.tools.notes_clarity.4}} & {{evaluation.tools.notes_clarity.5}} \\\\
    \\hline
    Penggunaan 'white board' & Jumlah Penilaian & {{evaluation.tools.whiteboard.1}} & {{evaluation.tools.whiteboard.2}} & {{evaluation.tools.whiteboard.3}} & {{evaluation.tools.whiteboard.4}} & {{evaluation.tools.whiteboard.5}} \\\\
    \\hline
    Sistem LCD & Jumlah Penilaian & {{evaluation.tools.lcd.1}} & {{evaluation.tools.lcd.2}} & {{evaluation.tools.lcd.3}} & {{evaluation.tools.lcd.4}} & {{evaluation.tools.lcd.5}} \\\\
    \\hline
    Penggunaan PA sistem & Jumlah Penilaian & {{evaluation.tools.pa_system.1}} & {{evaluation.tools.pa_system.2}} & {{evaluation.tools.pa_system.3}} & {{evaluation.tools.pa_system.4}} & {{evaluation.tools.pa_system.5}} \\\\
    \\hline
    \\multicolumn{7}{|c|}{\\textbf{C – Keberkesanan Penyampai}} \\\\
    \\hline
    Persediaan yang rapi & Jumlah Penilaian & {{evaluation.presenter.preparation.1}} & {{evaluation.presenter.preparation.2}} & {{evaluation.presenter.preparation.3}} & {{evaluation.presenter.preparation.4}} & {{evaluation.presenter.preparation.5}} \\\\
    \\hline
    Penyampaian yang teratur & Jumlah Penilaian & {{evaluation.presenter.delivery.1}} & {{evaluation.presenter.delivery.2}} & {{evaluation.presenter.delivery.3}} & {{evaluation.presenter.delivery.4}} & {{evaluation.presenter.delivery.5}} \\\\
    \\hline
    Bahasa mudah difahami & Jumlah Penilaian & {{evaluation.presenter.language.1}} & {{evaluation.presenter.language.2}} & {{evaluation.presenter.language.3}} & {{evaluation.presenter.language.4}} & {{evaluation.presenter.language.5}} \\\\
    \\hline
    Pengetahuan tajuk kursus & Jumlah Penilaian & {{evaluation.presenter.knowledge.1}} & {{evaluation.presenter.knowledge.2}} & {{evaluation.presenter.knowledge.3}} & {{evaluation.presenter.knowledge.4}} & {{evaluation.presenter.knowledge.5}} \\\\
    \\hline
    Menjawab soalan dengan baik & Jumlah Penilaian & {{evaluation.presenter.answering.1}} & {{evaluation.presenter.answering.2}} & {{evaluation.presenter.answering.3}} & {{evaluation.presenter.answering.4}} & {{evaluation.presenter.answering.5}} \\\\
    \\hline
    Metodologi latihan sesuai & Jumlah Penilaian & {{evaluation.presenter.methodology.1}} & {{evaluation.presenter.methodology.2}} & {{evaluation.presenter.methodology.3}} & {{evaluation.presenter.methodology.4}} & {{evaluation.presenter.methodology.5}} \\\\
    \\hline
    Menarik minat peserta & Jumlah Penilaian & {{evaluation.presenter.engagement.1}} & {{evaluation.presenter.engagement.2}} & {{evaluation.presenter.engagement.3}} & {{evaluation.presenter.engagement.4}} & {{evaluation.presenter.engagement.5}} \\\\
    \\hline
    Maklumbalas peserta & Jumlah Penilaian & {{evaluation.presenter.feedback.1}} & {{evaluation.presenter.feedback.2}} & {{evaluation.presenter.feedback.3}} & {{evaluation.presenter.feedback.4}} & {{evaluation.presenter.feedback.5}} \\\\
    \\hline
    \\multicolumn{7}{|c|}{\\textbf{D – Fasilitator}} \\\\
    \\hline
    Memberi impak kepada peserta & Jumlah Penilaian & {{evaluation.facilitator.impact.1}} & {{evaluation.facilitator.impact.2}} & {{evaluation.facilitator.impact.3}} & {{evaluation.facilitator.impact.4}} & {{evaluation.facilitator.impact.5}} \\\\
    \\hline
    Prestasi keseluruhan & Jumlah Penilaian & {{evaluation.facilitator.performance.1}} & {{evaluation.facilitator.performance.2}} & {{evaluation.facilitator.performance.3}} & {{evaluation.facilitator.performance.4}} & {{evaluation.facilitator.performance.5}} \\\\
    \\hline
    \\multicolumn{7}{|c|}{\\textbf{E – Persekitaran}} \\\\
    \\hline
    Lokasi kursus & Jumlah Penilaian & {{evaluation.environment.location.1}} & {{evaluation.environment.location.2}} & {{evaluation.environment.location.3}} & {{evaluation.environment.location.4}} & {{evaluation.environment.location.5}} \\\\
    \\hline
    Kemudahan tempat ibadah & Jumlah Penilaian & {{evaluation.environment.worship.1}} & {{evaluation.environment.worship.2}} & {{evaluation.environment.worship.3}} & {{evaluation.environment.worship.4}} & {{evaluation.environment.worship.5}} \\\\
    \\hline
    Kemudahan asas & Jumlah Penilaian & {{evaluation.environment.facilities.1}} & {{evaluation.environment.facilities.2}} & {{evaluation.environment.facilities.3}} & {{evaluation.environment.facilities.4}} & {{evaluation.environment.facilities.5}} \\\\
    \\hline
    Penyediaan makan/minuman & Jumlah Penilaian & {{evaluation.environment.catering.1}} & {{evaluation.environment.catering.2}} & {{evaluation.environment.catering.3}} & {{evaluation.environment.catering.4}} & {{evaluation.environment.catering.5}} \\\\
    \\hline
    Kemudahan dewan seminar & Jumlah Penilaian & {{evaluation.environment.seminar_hall.1}} & {{evaluation.environment.seminar_hall.2}} & {{evaluation.environment.seminar_hall.3}} & {{evaluation.environment.seminar_hall.4}} & {{evaluation.environment.seminar_hall.5}} \\\\
    \\hline
    \\multicolumn{7}{|c|}{\\textbf{F – Keseluruhan Kursus}} \\\\
    \\hline
    Memberi impak kepada peserta & Jumlah Penilaian & {{evaluation.overall.impact.1}} & {{evaluation.overall.impact.2}} & {{evaluation.overall.impact.3}} & {{evaluation.overall.impact.4}} & {{evaluation.overall.impact.5}} \\\\
    \\hline
    Prestasi keseluruhan & Jumlah Penilaian & {{evaluation.overall.performance.1}} & {{evaluation.overall.performance.2}} & {{evaluation.overall.performance.3}} & {{evaluation.overall.performance.4}} & {{evaluation.overall.performance.5}} \\\\
    \\hline
\\end{tabular}

% Section 5: Improvement Suggestions
\\section{Cadangan Penambahbaikan}
\\subsection{Cadangan Perunding}
\\begin{itemize}
    \\item {{suggestions.consultant}}
\\end{itemize}

\\subsection{Cadangan Asnaf/Peserta}
\\begin{itemize}
    \\item {{suggestions.participants}}
\\end{itemize}

% Section 6: Evaluation Summary
\\section{Rumusan Penilaian}
Penilaian dibuat berdasarkan borang penilaian yang diisi oleh {{evaluation.total_participants}} orang peserta. Penilaian merangkumi enam komponen: kandungan sesi, alat bantu mengajar, keberkesanan penyampaian, fasilitator, persekitaran, dan impak keseluruhan program. Skala penilaian adalah seperti berikut:

\\begin{tabular}{|c|c|c|c|c|}
    \\hline
    \\rowcolor{lightgray}
    \\textbf{1} & \\textbf{2} & \\textbf{3} & \\textbf{4} & \\textbf{5} \\\\
    \\hline
    Tidak Memuaskan & Kurang Memuaskan & Memuaskan & Baik & Cemerlang \\\\
    \\hline
\\end{tabular}

\\begin{tabular}{|c|c|c|c|c|c|}
    \\hline
    \\rowcolor{lightgray}
    \\textbf{Peratus} & \\textbf{Tidak Memuaskan} & \\textbf{Kurang Memuaskan} & \\textbf{Memuaskan} & \\textbf{Baik} & \\textbf{Cemerlang} \\\\
    \\hline
    & {{evaluation.summary.percentage.1}} & {{evaluation.summary.percentage.2}} & {{evaluation.summary.percentage.3}} & {{evaluation.summary.percentage.4}} & {{evaluation.summary.percentage.5}} \\\\
    \\hline
\\end{tabular}

% Placeholder for chart (to be generated by automation system)
% {{evaluation.chart}}

% Section 7: Pre and Post Analysis
\\section{Analisa Pra dan Post}
\\subsection{Pra Penilaian Peserta}
\\begin{longtable}{|c|p{6cm}|c|}
    \\hline
    \\rowcolor{lightgray}
    \\textbf{Bil} & \\textbf{Nama} & \\textbf{Markah Pra} \\\\
    \\hline
    \\endhead
    {{#participants}}
    {{participant.bil}} & {{participant.name}} & {{participant.pre_mark}} \\\\
    \\hline
    {{/participants}}
\\end{longtable}

\\subsection{Post Penilaian Peserta}
\\begin{longtable}{|c|p{6cm}|c|}
    \\hline
    \\rowcolor{lightgray}
    \\textbf{Bil} & \\textbf{Nama} & \\textbf{Markah Post} \\\\
    \\hline
    \\endhead
    {{#participants}}
    {{participant.bil}} & {{participant.name}} & {{participant.post_mark}} \\\\
    \\hline
    {{/participants}}
\\end{longtable}

\\subsection{Analisa Pra dan Post}
\\begin{longtable}{|c|p{6cm}|c|c|c|}
    \\hline
    \\rowcolor{lightgray}
    \\textbf{Bil} & \\textbf{Nama} & \\textbf{Markah Pra} & \\textbf{Markah Post} & \\textbf{Kenaikan/Penurunan} \\\\
    \\hline
    \\endhead
    {{#participants}}
    {{participant.bil}} & {{participant.name}} & {{participant.pre_mark}} & {{participant.post_mark}} & {{participant.change}} \\\\
    \\hline
    {{/participants}}
\\end{longtable}

\\subsection{Rumusan Penilaian Pra Post}
\\begin{tabular}{|c|c|c|c|c|}
    \\hline
    \\rowcolor{lightgray}
    \\textbf{} & \\textbf{Menurun} & \\textbf{Tiada Peningkatan} & \\textbf{Meningkat} & \\textbf{Tidak Lengkap} \\\\
    \\hline
    Peratus & {{evaluation.pre_post.decrease.percentage}} & {{evaluation.pre_post.no_change.percentage}} & {{evaluation.pre_post.increase.percentage}} & {{evaluation.pre_post.incomplete.percentage}} \\\\
    \\hline
    Orang & {{evaluation.pre_post.decrease.count}} & {{evaluation.pre_post.no_change.count}} & {{evaluation.pre_post.increase.count}} & {{evaluation.pre_post.incomplete.count}} \\\\
    \\hline
\\end{tabular}

% Section 8: Attendance Report
\\section{Laporan Kehadiran Peserta}
\\begin{longtable}{|c|p{4cm}|p{3cm}|p{4cm}|p{2cm}|c|c|p{2cm}|}
    \\hline
    \\rowcolor{lightgray}
    \\textbf{Bil} & \\textbf{Nama} & \\textbf{No. K/P} & \\textbf{Alamat} & \\textbf{No. Tel} & \\textbf{Hadir H1} & \\textbf{Hadir H2} & \\textbf{Catatan} \\\\
    \\hline
    \\endhead
    {{#participants}}
    {{participant.bil}} & {{participant.name}} & {{participant.ic}} & {{participant.address}} & {{participant.tel}} & {{participant.attendance_day1}} & {{participant.attendance_day2}} & {{participant.notes}} \\\\
    \\hline
    {{/participants}}
\\end{longtable}

\\textbf{Jumlah Jemputan:} {{attendance.total_invited}} \\\\
\\textbf{Jumlah Kehadiran:} {{attendance.total_attended}} \\\\
\\textbf{Jumlah Tidak Hadir:} {{attendance.total_absent}}

% Section 9: Individual Asnaf Evaluation
\\section{Laporan Penilaian Asnaf Individu}
Penilaian dibuat berdasarkan {{evaluation.total_participants}} orang peserta yang hadir pada hari kedua. Penilaian merangkumi tiga komponen: kandungan sesi, keberkesanan penyampaian, dan impak keseluruhan program. Maklum balas ini boleh digunakan untuk penambahbaikan program akan datang.

% Section 10: Program Pictures
\\section{Gambar Program}
\\begin{figure}[h]
    \\centering
    {{#images}}
    \\includegraphics[width=0.45\\textwidth]{{image.path}}
    \\caption{{image.caption}}
    \\vspace{0.5cm}
    {{/images}}
\\end{figure}

% Section 11: Conclusion
\\section{Kesimpulan}
{{program.conclusion}}

% Signatures
\\begin{center}
    \\vspace{1cm}
    \\begin{tabular}{p{5cm}p{5cm}p{5cm}}
        \\textbf{Disediakan Oleh:} & \\textbf{Disemak Oleh:} & \\textbf{Disahkan Oleh:} \\\\
        Perunding (MUBARAK RESOURCES) & Eksekutif Pembangunan Asnaf & Ketua Jabatan Pembangunan Insan dan Ekonomi \\\\
        {{signature.consultant.name}} & {{signature.executive.name}} & {{signature.head.name}} \\\\
        Tarikh: {{program.date}} & Tarikh: {{program.date}} & Tarikh: {{program.date}} \\\\
    \\end{tabular}
\\end{center}

\\end{document}`,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      },
      {
        id: '2',
        name: 'Jinja2 Report Template',
        type: 'jinja2',
        description: 'Flexible Jinja2 template for dynamic report generation',
        content: `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ report.title }} - {{ report.date }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; }
        .section { margin: 30px 0; }
        .section h2 { color: #2c3e50; border-left: 4px solid #3498db; padding-left: 15px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #f8f9fa; font-weight: bold; }
        .highlight { background-color: #fff3cd; padding: 10px; border-radius: 5px; }
        .footer { margin-top: 50px; text-align: center; color: #666; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ report.title }}</h1>
        <p><strong>Date:</strong> {{ report.date }}</p>
        <p><strong>Location:</strong> {{ report.location }}</p>
        <p><strong>Organizer:</strong> {{ report.organizer }}</p>
    </div>

    <div class="section">
        <h2>Executive Summary</h2>
        <p>{{ report.summary }}</p>
    </div>

    <div class="section">
        <h2>Program Details</h2>
        <table>
            <tr>
                <th>Program Name</th>
                <td>{{ program.name }}</td>
            </tr>
            <tr>
                <th>Duration</th>
                <td>{{ program.duration }}</td>
            </tr>
            <tr>
                <th>Participants</th>
                <td>{{ program.participants_count }}</td>
            </tr>
            <tr>
                <th>Facilitator</th>
                <td>{{ program.facilitator }}</td>
            </tr>
        </table>
    </div>

    {% if program.schedule %}
    <div class="section">
        <h2>Program Schedule</h2>
        <table>
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Activity</th>
                    <th>Description</th>
                    <th>Facilitator</th>
                </tr>
            </thead>
            <tbody>
                {% for session in program.schedule %}
                <tr>
                    <td>{{ session.time }}</td>
                    <td>{{ session.activity }}</td>
                    <td>{{ session.description }}</td>
                    <td>{{ session.facilitator }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% endif %}

    {% if evaluation %}
    <div class="section">
        <h2>Evaluation Results</h2>
        <div class="highlight">
            <p><strong>Overall Rating:</strong> {{ evaluation.overall_rating }}/5</p>
            <p><strong>Total Responses:</strong> {{ evaluation.total_responses }}</p>
        </div>
        
        {% if evaluation.categories %}
        <table>
            <thead>
                <tr>
                    <th>Category</th>
                    <th>Average Rating</th>
                    <th>Comments</th>
                </tr>
            </thead>
            <tbody>
                {% for category in evaluation.categories %}
                <tr>
                    <td>{{ category.name }}</td>
                    <td>{{ category.rating }}/5</td>
                    <td>{{ category.comments }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endif %}
    </div>
    {% endif %}

    {% if recommendations %}
    <div class="section">
        <h2>Recommendations</h2>
        <ul>
            {% for rec in recommendations %}
            <li>{{ rec.description }}</li>
            {% endfor %}
        </ul>
    </div>
    {% endif %}

    <div class="footer">
        <p>Report generated on {{ report.generated_at }}</p>
        <p>Prepared by: {{ report.prepared_by }}</p>
    </div>
</body>
</html>`,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }
    ];
    setTemplates(defaultTemplates);
  };

  const handleEditTemplate = (template: Template) => {
    setEditingTemplate(template);
    setShowEditor(true);
  };

  const handleDeleteTemplate = (templateId: string) => {
    setTemplates(templates.filter(t => t.id !== templateId));
  };

  const handleDownloadTemplate = (template: Template) => {
    // Download template content
    const blob = new Blob([template.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${template.name}.${template.type}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleViewTemplate = (template: Template) => {
    setSelectedTemplate(template);
    setShowViewer(true);
  };

  const handleSaveTemplate = (template: Template) => {
    if (editingTemplate) {
      // Update existing template
      setTemplates(templates.map(t => t.id === template.id ? template : t));
    } else {
      // Add new template
      setTemplates([...templates, template]);
    }
    setShowEditor(false);
    setEditingTemplate(null);
  };

  const handleCancelEdit = () => {
    setShowEditor(false);
    setEditingTemplate(null);
  };

  const handleCloseViewer = () => {
    setShowViewer(false);
    setSelectedTemplate(null);
  };

  const handleCreateNew = () => {
    setEditingTemplate(null);
    setShowEditor(true);
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'latex':
        return theme.palette.primary.main;
      case 'jinja2':
        return theme.palette.secondary.main;
      case 'docx':
        return theme.palette.success.main;
      default:
        return theme.palette.grey[500];
    }
  };

  if (showEditor) {
    return (
      <TemplateEditor
        template={editingTemplate || undefined}
        onSave={handleSaveTemplate}
        onCancel={handleCancelEdit}
      />
    );
  }

  if (showViewer && selectedTemplate) {
    return (
      <TemplateViewer
        template={selectedTemplate}
        onClose={handleCloseViewer}
        onEdit={handleEditTemplate}
      />
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Template Manager
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Upload />}
            onClick={() => setActiveTab(1)}
          >
            Import/Export
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={handleCreateNew}
          >
            Create Template
          </Button>
        </Box>
      </Box>

      <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
        <Tab label="Templates" />
        <Tab label="Import/Export" />
      </Tabs>

      {activeTab === 1 && (
        <TemplateImportExport onTemplatesImported={(templates) => setTemplates(templates)} />
      )}

      {activeTab === 0 && (

      <Grid container spacing={3}>
        {templates.map((template) => (
          <Grid item xs={12} md={6} lg={4} key={template.id}>
            <Card 
              sx={{ 
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                '&:hover': {
                  boxShadow: theme.shadows[8],
                  transform: 'translateY(-2px)',
                  transition: 'all 0.3s ease-in-out'
                }
              }}
            >
              <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" component="h2" sx={{ flexGrow: 1 }}>
                    {template.name}
                  </Typography>
                  <Chip
                    label={template.type.toUpperCase()}
                    size="small"
                    sx={{ 
                      backgroundColor: getTypeColor(template.type),
                      color: 'white',
                      fontWeight: 'bold'
                    }}
                  />
                </Box>
                
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2, flexGrow: 1 }}>
                  {template.description}
                </Typography>

                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="caption" color="text.secondary">
                    Updated: {new Date(template.updatedAt).toLocaleDateString()}
                  </Typography>
                  
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Tooltip title="View Template">
                      <IconButton
                        size="small"
                        onClick={() => handleViewTemplate(template)}
                        color="primary"
                      >
                        <Visibility />
                      </IconButton>
                    </Tooltip>
                    
                    <Tooltip title="Edit Template">
                      <IconButton
                        size="small"
                        onClick={() => handleEditTemplate(template)}
                        color="secondary"
                      >
                        <Edit />
                      </IconButton>
                    </Tooltip>
                    
                    <Tooltip title="Download Template">
                      <IconButton
                        size="small"
                        onClick={() => handleDownloadTemplate(template)}
                        color="success"
                      >
                        <Download />
                      </IconButton>
                    </Tooltip>
                    
                    <Tooltip title="Delete Template">
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteTemplate(template.id)}
                        color="error"
                      >
                        <Delete />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {templates.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No templates found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Create your first template to get started
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default TemplateManager;
