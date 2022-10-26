import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CustomSingleSelectComponent } from './custom-single-select.component';

describe('CustomSingleSelectComponent', () => {
  let component: CustomSingleSelectComponent;
  let fixture: ComponentFixture<CustomSingleSelectComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ CustomSingleSelectComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(CustomSingleSelectComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
