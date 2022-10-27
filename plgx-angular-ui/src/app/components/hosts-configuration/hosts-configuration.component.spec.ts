import { ComponentFixture, TestBed } from '@angular/core/testing';

import { HostsConfigurationComponent } from './hosts-configuration.component';

describe('HostsConfigurationComponent', () => {
  let component: HostsConfigurationComponent;
  let fixture: ComponentFixture<HostsConfigurationComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ HostsConfigurationComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(HostsConfigurationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
