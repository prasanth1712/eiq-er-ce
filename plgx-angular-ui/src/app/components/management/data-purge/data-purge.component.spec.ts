import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { DataPurgeComponent } from './data-purge.component';

describe('DataPurgeComponent', () => {
  let component: DataPurgeComponent;
  let fixture: ComponentFixture<DataPurgeComponent>;

  beforeEach(waitForAsync(() => {
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
