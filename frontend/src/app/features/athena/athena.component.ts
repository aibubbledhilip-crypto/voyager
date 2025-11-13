import { Component, OnInit, ViewChild } from '@angular/core';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';
import { MatSnackBar } from '@angular/material/snack-bar';
import { AthenaService, Database, Table, QueryResult, SystemSettings } from './athena.service';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-athena',
  templateUrl: './athena.component.html',
  styleUrls: ['./athena.component.scss']
})
export class AthenaComponent implements OnInit {
  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  // Query editor
  query: string = 'SELECT * FROM your_table LIMIT 10;';
  selectedDatabase: string = '';

  // Loading states
  loadingDatabases = false;
  loadingTables = false;
  executingQuery = false;
  downloadingResults = false;

  // Data
  databases: Database[] = [];
  tables: Table[] = [];
  queryResults: QueryResult | null = null;

  // Table
  displayedColumns: string[] = [];
  dataSource = new MatTableDataSource<any>([]);

  // Admin settings
  showAdminPanel = false;
  systemSettings: SystemSettings | null = null;
  downloadLimit: number = 100000;
  displayLimit: number = 1000;
  savingSettings = false;

  // Statistics
  executionTime: string = '';
  bytesScanned: string = '';
  rowCount: number = 0;

  constructor(
    private athenaService: AthenaService,
    public authService: AuthService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.loadDatabases();
    if (this.authService.isAdmin) {
      this.loadAdminSettings();
    }
  }

  // Database operations
  loadDatabases(): void {
    this.loadingDatabases = true;
    this.athenaService.listDatabases().subscribe({
      next: (databases) => {
        this.databases = databases;
        if (databases.length > 0 && !this.selectedDatabase) {
          this.selectedDatabase = databases[0].name;
          this.loadTables(this.selectedDatabase);
        }
        this.loadingDatabases = false;
      },
      error: (error) => {
        this.showError('Failed to load databases: ' + (error.error?.detail || error.message));
        this.loadingDatabases = false;
      }
    });
  }

  loadTables(database: string): void {
    if (!database) return;

    this.loadingTables = true;
    this.athenaService.listTables(database).subscribe({
      next: (tables) => {
        this.tables = tables;
        this.loadingTables = false;
      },
      error: (error) => {
        this.showError('Failed to load tables: ' + (error.error?.detail || error.message));
        this.loadingTables = false;
      }
    });
  }

  onDatabaseChange(database: string): void {
    this.selectedDatabase = database;
    this.loadTables(database);
  }

  insertTableName(tableName: string): void {
    // Insert table name at cursor position in query
    const textarea = document.querySelector('textarea') as HTMLTextAreaElement;
    if (textarea) {
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const text = this.query;
      this.query = text.substring(0, start) + tableName + text.substring(end);

      // Set cursor position after inserted text
      setTimeout(() => {
        textarea.focus();
        textarea.setSelectionRange(start + tableName.length, start + tableName.length);
      }, 0);
    } else {
      this.query += ' ' + tableName;
    }
  }

  // Query execution
  executeQuery(): void {
    if (!this.query.trim()) {
      this.showError('Please enter a query');
      return;
    }

    this.executingQuery = true;
    this.queryResults = null;
    this.dataSource.data = [];

    const request = {
      query: this.query.trim(),
      database: this.selectedDatabase || undefined
    };

    this.athenaService.executeQuery(request).subscribe({
      next: (result) => {
        this.queryResults = result;
        this.displayedColumns = result.columns;

        // Convert rows to objects for Material table
        const data = result.rows.map(row => {
          const obj: any = {};
          result.columns.forEach((col, index) => {
            obj[col] = row[index];
          });
          return obj;
        });

        this.dataSource.data = data;
        this.dataSource.paginator = this.paginator;
        this.dataSource.sort = this.sort;

        // Update statistics
        this.executionTime = result.execution_time.toFixed(2) + 's';
        this.bytesScanned = this.formatBytes(result.bytes_scanned);
        this.rowCount = result.row_count;

        this.executingQuery = false;
        this.showSuccess(`Query executed successfully. ${result.row_count} rows returned.`);
      },
      error: (error) => {
        this.executingQuery = false;
        const errorMessage = error.error?.detail || error.message || 'Unknown error';
        this.showError('Query execution failed: ' + errorMessage);
      }
    });
  }

  downloadResults(): void {
    if (!this.query.trim()) {
      this.showError('Please enter a query');
      return;
    }

    this.downloadingResults = true;

    const request = {
      query: this.query.trim(),
      database: this.selectedDatabase || undefined
    };

    this.athenaService.downloadQueryResults(request).subscribe({
      next: (blob) => {
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
        a.download = `athena_results_${timestamp}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        this.downloadingResults = false;
        this.showSuccess('Results downloaded successfully');
      },
      error: (error) => {
        this.downloadingResults = false;
        const errorMessage = error.error?.detail || 'Unknown error';
        this.showError('Download failed: ' + errorMessage);
      }
    });
  }

  clearQuery(): void {
    this.query = '';
  }

  // Admin operations
  loadAdminSettings(): void {
    this.athenaService.getAdminSettings().subscribe({
      next: (settings) => {
        this.systemSettings = settings;
        this.downloadLimit = settings.athena_max_download_rows;
        this.displayLimit = settings.athena_display_rows;
      },
      error: (error) => {
        console.error('Failed to load admin settings:', error);
      }
    });
  }

  updateDownloadLimit(): void {
    if (this.downloadLimit < 1000 || this.downloadLimit > 1000000) {
      this.showError('Download limit must be between 1,000 and 1,000,000');
      return;
    }

    this.savingSettings = true;
    this.athenaService.updateDownloadLimit(this.downloadLimit).subscribe({
      next: (response) => {
        this.showSuccess('Download limit updated to ' + response.new_value.toLocaleString());
        this.savingSettings = false;
      },
      error: (error) => {
        this.showError('Failed to update download limit: ' + (error.error?.detail || error.message));
        this.savingSettings = false;
      }
    });
  }

  updateDisplayLimit(): void {
    if (this.displayLimit < 10 || this.displayLimit > 10000) {
      this.showError('Display limit must be between 10 and 10,000');
      return;
    }

    this.savingSettings = true;
    this.athenaService.updateDisplayLimit(this.displayLimit).subscribe({
      next: (response) => {
        this.showSuccess('Display limit updated to ' + response.new_value.toLocaleString());
        this.savingSettings = false;
      },
      error: (error) => {
        this.showError('Failed to update display limit: ' + (error.error?.detail || error.message));
        this.savingSettings = false;
      }
    });
  }

  // Utility functions
  formatBytes(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  }

  showSuccess(message: string): void {
    this.snackBar.open(message, 'Close', {
      duration: 5000,
      panelClass: ['success-snackbar'],
      horizontalPosition: 'end',
      verticalPosition: 'top'
    });
  }

  showError(message: string): void {
    this.snackBar.open(message, 'Close', {
      duration: 7000,
      panelClass: ['error-snackbar'],
      horizontalPosition: 'end',
      verticalPosition: 'top'
    });
  }

  // Sample queries
  setSampleQuery(type: string): void {
    switch (type) {
      case 'select':
        this.query = 'SELECT * FROM your_table LIMIT 10;';
        break;
      case 'count':
        this.query = 'SELECT COUNT(*) as total FROM your_table;';
        break;
      case 'aggregate':
        this.query = 'SELECT column_name, COUNT(*) as count\nFROM your_table\nGROUP BY column_name\nORDER BY count DESC\nLIMIT 10;';
        break;
      case 'join':
        this.query = 'SELECT t1.*, t2.column\nFROM table1 t1\nJOIN table2 t2 ON t1.id = t2.table1_id\nLIMIT 10;';
        break;
    }
  }
}
