import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';

interface Module {
  title: string;
  description: string;
  icon: string;
  route: string;
  badge: string;
  badgeColor: string;
  features: string[];
  adminOnly: boolean;
  comingSoon: boolean;
}

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {
  modules: Module[] = [
    {
      title: 'Intelligent RAG Data Analysis',
      description: 'AI-powered data analysis using Retrieval Augmented Generation. Upload files and get instant insights.',
      icon: 'analytics',
      route: '/data-analysis',
      badge: 'Active',
      badgeColor: 'success',
      features: [
        'Upload 50+ CSV/Excel files',
        'Natural language queries',
        'AI-powered insights',
        'Interactive visualizations'
      ],
      adminOnly: false,
      comingSoon: true
    },
    {
      title: 'SQL Athena Query Runner',
      description: 'Execute SQL queries against AWS Athena database. Browse databases, tables, and run queries with instant results.',
      icon: 'search',
      route: '/athena',
      badge: 'Active',
      badgeColor: 'success',
      features: [
        'Execute SQL queries',
        'Browse databases & tables',
        'Download results as CSV',
        'Admin-configurable limits'
      ],
      adminOnly: false,
      comingSoon: false
    },
    {
      title: 'Admin Dashboard',
      description: 'Complete user management, system monitoring, and administrative controls.',
      icon: 'settings',
      route: '/admin',
      badge: 'Admin Only',
      badgeColor: 'admin',
      features: [
        'User management (CRUD)',
        'System statistics',
        'Access control',
        'Password management'
      ],
      adminOnly: true,
      comingSoon: true
    },
    {
      title: 'Business Intelligence',
      description: 'Advanced analytics and reporting dashboards for business insights.',
      icon: 'trending_up',
      route: '',
      badge: 'Coming Soon',
      badgeColor: 'coming',
      features: [
        'Interactive dashboards',
        'Custom reports',
        'KPI tracking',
        'Export capabilities'
      ],
      adminOnly: false,
      comingSoon: true
    },
    {
      title: 'AI Assistant',
      description: 'Conversational AI assistant for workflow automation and support.',
      icon: 'smart_toy',
      route: '',
      badge: 'Coming Soon',
      badgeColor: 'coming',
      features: [
        'Natural conversations',
        'Task automation',
        'Knowledge base',
        'Multi-language support'
      ],
      adminOnly: false,
      comingSoon: true
    },
    {
      title: 'Document Processing',
      description: 'Automated document analysis, extraction, and classification.',
      icon: 'description',
      route: '',
      badge: 'Coming Soon',
      badgeColor: 'coming',
      features: [
        'OCR & extraction',
        'Auto-classification',
        'Entity recognition',
        'Batch processing'
      ],
      adminOnly: false,
      comingSoon: true
    }
  ];

  visibleModules: Module[] = [];

  constructor(
    public authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.visibleModules = this.modules.filter(
      module => !module.adminOnly || this.authService.isAdmin
    );
  }

  navigateToModule(module: Module): void {
    if (!module.comingSoon && module.route) {
      this.router.navigate([module.route]);
    }
  }

  getBadgeClass(color: string): string {
    return `badge-${color}`;
  }
}
