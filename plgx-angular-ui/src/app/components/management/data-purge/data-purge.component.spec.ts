import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DataPurgeComponent } from './data-purge.component';

describe('DataPurgeComponent', () => {
  let component: DataPurgeComponent;
  let fixture: ComponentFixture<DataPurgeComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DataPurgeComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DataPurgeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
