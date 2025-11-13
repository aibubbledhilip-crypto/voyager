import { Component, Output, EventEmitter, Input } from '@angular/core';

@Component({
  selector: 'app-file-uploader',
  templateUrl: './file-uploader.component.html',
  styleUrls: ['./file-uploader.component.scss']
})
export class FileUploaderComponent {
  @Input() accept: string = '.csv,.xlsx,.xls';
  @Input() multiple: boolean = true;
  @Input() maxSize: number = 100 * 1024 * 1024; // 100MB
  @Output() filesSelected = new EventEmitter<File[]>();

  isDragging = false;
  selectedFiles: File[] = [];

  onFileSelect(event: any): void {
    const files = Array.from(event.target.files) as File[];
    this.handleFiles(files);
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = true;
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;

    const files = Array.from(event.dataTransfer?.files || []) as File[];
    this.handleFiles(files);
  }

  private handleFiles(files: File[]): void {
    // Filter by accepted types
    const validFiles = files.filter(file => {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      return this.accept.includes(ext);
    });

    // Check file size
    const sizeValidFiles = validFiles.filter(file => file.size <= this.maxSize);

    if (sizeValidFiles.length > 0) {
      this.selectedFiles = this.multiple
        ? [...this.selectedFiles, ...sizeValidFiles]
        : [sizeValidFiles[0]];

      this.filesSelected.emit(this.selectedFiles);
    }
  }

  removeFile(index: number): void {
    this.selectedFiles.splice(index, 1);
    this.filesSelected.emit(this.selectedFiles);
  }

  clearFiles(): void {
    this.selectedFiles = [];
    this.filesSelected.emit(this.selectedFiles);
  }
}
