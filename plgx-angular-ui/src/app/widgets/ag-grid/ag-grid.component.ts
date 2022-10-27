import { Component, OnChanges, Input, Output, ViewChild, OnInit } from '@angular/core';
import { Subject, Observable } from 'rxjs';

@Component({
  selector: 'app-ag-grid',
  templateUrl: './ag-grid.component.html',
  styleUrls: ['./ag-grid.component.css']
})
export class AgGridComponent implements OnInit {

  @Input() GridData: any;
  @Input() ColData: any;
  @Input() dtOptions: DataTables.Settings = {};
  @Input() dtTrigger: Subject<any> = new Subject();
  constructor() { }

  ngOnInit(): void {
  }

}
