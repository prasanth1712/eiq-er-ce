var __assign = (this && this.__assign) || Object.assign || function(t) {
    for (var s, i = 1, n = arguments.length; i < n; i++) {
        s = arguments[i];
        for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
            t[p] = s[p];
    }
    return t;
};

import { NG_VALUE_ACCESSOR, NG_VALIDATORS } from '@angular/forms';
import { QueryOperatorDirective } from './query-operator.directive';
import { QueryFieldDirective } from './query-field.directive';
import { QueryEntityDirective } from './query-entity.directive';
import { QuerySwitchGroupDirective } from './query-switch-group.directive';
import { QueryButtonGroupDirective } from './query-button-group.directive';
import { QueryInputDirective } from './query-input.directive';
import { QueryRemoveButtonDirective } from './query-remove-button.directive';
import { QueryEmptyWarningDirective } from './query-empty-warning.directive';
import { QueryArrowIconDirective } from './query-arrow-icon.directive';
import { ChangeDetectorRef, Component, ContentChild, ContentChildren, forwardRef, Input, ViewChild, ɵConsole } from '@angular/core';
export var CONTROL_VALUE_ACCESSOR = {
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(function () { return QueryBuilderComponent; }),
    multi: true
};
export var VALIDATOR = {
    provide: NG_VALIDATORS,
    useExisting: forwardRef(function () { return QueryBuilderComponent; }),
    multi: true
};
var QueryBuilderComponent = /** @class */ (function () {
    function QueryBuilderComponent(changeDetectorRef) {
        var _this = this;
        this.changeDetectorRef = changeDetectorRef;
        this.defaultClassNames = {
            arrowIconButton: 'q-arrow-icon-button',
            arrowIcon: 'q-icon q-arrow-icon',
            removeIcon: 'q-icon q-remove-icon',
            addIcon: 'q-icon q-add-icon',
            button: 'q-button',
            buttonGroup: 'q-button-group',
            removeButton: 'q-remove-button',
            switchGroup: 'q-switch-group',
            switchLabel: 'q-switch-label',
            switchRadio: 'q-switch-radio',
            rightAlign: 'q-right-align',
            transition: 'q-transition',
            collapsed: 'q-collapsed',
            treeContainer: 'q-tree-container',
            tree: 'q-tree',
            row: 'q-row',
            connector: 'q-connector',
            rule: 'q-rule',
            ruleSet: 'q-ruleset',
            invalidRuleSet: 'q-invalid-ruleset',
            emptyWarning: 'q-empty-warning',
            fieldControl: 'q-field-control',
            fieldControlSize: 'q-control-size',
            entityControl: 'q-entity-control',
            entityControlSize: 'q-control-size',
            operatorControl: 'q-operator-control',
            operatorControlSize: 'q-control-size',
            inputControl: 'q-input-control',
            inputControlSize: 'q-control-size'
        };
        this.defaultOperatorMap = {
            string: ['=', '!=', 'contains', 'like'],
            number: ['=', '!=', '>', '>=', '<', '<='],
            time: ['=', '!=', '>', '>=', '<', '<='],
            date: ['=', '!=', '>', '>=', '<', '<='],
            category: ['=', '!=', 'in', 'not in'],
            boolean: ['=']
        };
        this.data = { condition: 'and', rules: [] };
        this.allowRuleset = true;
        this.allowCollapse = false;
        this.emptyMessage = 'A ruleset cannot be empty. Please add a rule or remove it all together.';
        this.config = { fields: {} };
        this.defaultTemplateTypes = [
            'string', 'number', 'time', 'date', 'category', 'boolean', 'multiselect', 'column'
        ];
        this.defaultEmptyList = [];
        this.inputContextCache = new Map();
        this.operatorContextCache = new Map();
        this.fieldContextCache = new Map();
        this.entityContextCache = new Map();
        this.removeButtonContextCache = new Map();
        // ----------END----------
        this.getDisabledState = function () {
            return _this.disabled;
        };
    }
    // ----------OnInit Implementation----------
    QueryBuilderComponent.prototype.ngOnInit = function () { };
    // ----------OnChanges Implementation----------
    QueryBuilderComponent.prototype.ngOnChanges = function (changes) {
        var config = this.config;
        var type = typeof config;
        if (type === 'object') {
            this.fields = Object.keys(config.fields).map(function (value) {

                var field = config.fields[value];
                field.value = field.value || value;
                return field;
            });
            if (config.entities) {
                this.entities = Object.keys(config.entities).map(function (value) {
                    var entity = config.entities[value];
                    entity.value = entity.value || value;
                    return entity;
                });
            }
            else {
                this.entities = null;
            }
            this.operatorsCache = {};
        }
        else {
            throw new Error("Expected 'config' must be a valid object, got " + type + " instead.");
        }
    };
    // ----------Validator Implementation----------
    QueryBuilderComponent.prototype.validate = function (control) {
        var errors = {};
        var ruleErrorStore = [];
        var hasErrors = false;
        if (!this.config.allowEmptyRulesets && this.checkEmptyRuleInRuleset(this.data)) {
            errors.empty = 'Empty rulesets are not allowed.';
            hasErrors = true;
        }
        this.validateRulesInRuleset(this.data, ruleErrorStore);
        if (ruleErrorStore.length) {
            errors.rules = ruleErrorStore;
            hasErrors = true;
        }
        return hasErrors ? errors : null;
    };
    Object.defineProperty(QueryBuilderComponent.prototype, "value", {
        // ----------ControlValueAccessor Implementation----------
        get: function () {
            return this.data;
        },
        set: function (value) {
            // When component is initialized without a formControl, null is passed to value
            this.data = value || { condition: 'and', rules: [] };
            this.handleDataChange();
        },
        enumerable: true,
        configurable: true
    });
    QueryBuilderComponent.prototype.writeValue = function (obj) {
        this.value = obj;
    };
    QueryBuilderComponent.prototype.registerOnChange = function (fn) {
        var _this = this;
        this.onChangeCallback = function () { return fn(_this.data); };
    };
    QueryBuilderComponent.prototype.registerOnTouched = function (fn) {
        var _this = this;
        this.onTouchedCallback = function () { return fn(_this.data); };
    };
    QueryBuilderComponent.prototype.setDisabledState = function (isDisabled) {
        this.disabled = isDisabled;
        this.changeDetectorRef.detectChanges();
    };
    QueryBuilderComponent.prototype.findTemplateForRule = function (rule) {
        // rule.value.push(rule.value1);
        //  rule.values = [rule.value, rule.value1];
        var type = this.getInputType(rule.field, rule.operator, rule.value);
        var rule_value = rule.value;
        // rule_value.push(rule.value1);
        console.log(rule_value);
        if (type) {
            var queryInput = this.findQueryInput(type);
            if (queryInput) {
                return queryInput.template;
            }
            else {
                if (this.defaultTemplateTypes.indexOf(type) === -1) {
                    console.warn("Could not find template for field with type: " + type);
                }
                return null;
            }
        }
    };
    QueryBuilderComponent.prototype.findQueryInput = function (type) {
        var templates = this.parentInputTemplates || this.inputTemplates;
       
        return templates.find(function (item) { return item.queryInputType === type; });
    };
    QueryBuilderComponent.prototype.getOperators = function (field) {
        
        if (this.operatorsCache[field]) {
            return this.operatorsCache[field];
        }
        var operators = this.defaultEmptyList;
        var fieldObject = this.config.fields[field];
        console.log(field);
        if (this.config.getOperators) {
            return this.config.getOperators(field, fieldObject);
        }
        var type = fieldObject.type;
        if (fieldObject && fieldObject.operators) {
            operators = fieldObject.operators;
        }
        else if (type) {
            operators = (this.operatorMap && this.operatorMap[type]) || this.defaultOperatorMap[type] || this.defaultEmptyList;
            if (operators.length === 0) {
                console.warn("No operators found for field '" + field + "' with type " + fieldObject.type + ". " +
                    "Please define an 'operators' property on the field or use the 'operatorMap' binding to fix this.");
            }
            if (fieldObject.nullable) {
                operators = operators.concat(['is null', 'is not null']);
            }
        }
        else {
            console.warn("No 'type' property found on field: '" + field + "'");
        }
        // Cache reference to array object, so it won't be computed next time and trigger a rerender.
        this.operatorsCache[field] = operators;
        return operators;
    };
    QueryBuilderComponent.prototype.getFields = function (entity) {
        if (this.entities && entity) {
            return this.fields.filter(function (field) {
                return field && field.entity === entity;
            });
        }
        else {
            return this.fields;
        }
    };
    QueryBuilderComponent.prototype.getInputType = function (field, operator) {
        console.log(field);
        if (this.config.getInputType) {
            return this.config.getInputType(field, operator);
        }
        if (!this.config.fields[field]) {
            throw new Error("No configuration for field '" + field + "' could be found! Please add it to config.fields.");
        }
        var type = this.config.fields[field].type;
        switch (operator) {
            case 'is null':
            case 'is not null':
                return null; // No displayed component
            case 'in':
            case 'not in':
                return type === 'category' || type === 'boolean' ? 'multiselect' : type;
            default:
                return type;
        }
    };
    QueryBuilderComponent.prototype.getOptions = function (field) {
    console.log(field);
        if (this.config.getOptions) {
            return this.config.getOptions(field);
        }
        return this.config.fields[field].options || this.defaultEmptyList;
    };
    QueryBuilderComponent.prototype.getClassNames = function () {
        var _this = this;
        var args = [];
        for (var _i = 0; _i < arguments.length; _i++) {
            args[_i] = arguments[_i];
        }
        var clsLookup = this.classNames ? this.classNames : this.defaultClassNames;
        var classNames = args.map(function (id) { return clsLookup[id] || _this.defaultClassNames[id]; }).filter(function (c) { return !!c; });
        return classNames.length ? classNames.join(' ') : null;
    };
    QueryBuilderComponent.prototype.getDefaultField = function (entity) {
        console.log(entity);
        if (!entity) {
            return null;
        }
        else if (entity.defaultField !== undefined) {
            return this.getDefaultValue(entity.defaultField);
        }
        else {
            var entityFields = this.fields.filter(function (field) {
                return field && field.entity === entity.value;
            });
            if (entityFields && entityFields.length) {
                return entityFields[0];
            }
            else {
                console.warn("No fields found for entity '" + entity.name + "'. " +
                    "A 'defaultOperator' is also not specified on the field config. Operator value will default to null.");
                return null;
            }
        }
    };
    QueryBuilderComponent.prototype.getDefaultOperator = function (field) {
        console.log(field)
        if (field && field.defaultOperator !== undefined) {
            return this.getDefaultValue(field.defaultOperator);
        }
        else {
            var operators = this.getOperators(field.value);
            if (operators && operators.length) {
                return operators[0];
            }
            else {
                console.warn("No operators found for field '" + field.value + "'. " +
                    "A 'defaultOperator' is also not specified on the field config. Operator value will default to null.");
                return null;
            }
        }
    };
    QueryBuilderComponent.prototype.addRule = function (parent) {
        
        if (this.disabled) {
            return;
        }
        parent = parent || this.data;
        if (this.config.addRule) {
            this.config.addRule(parent);
        }
        else {
            var field = this.fields[0];
            console.log(field.defaultValue);
            parent.rules = parent.rules.concat([{
                    field: field.value,
                    operator: this.getDefaultOperator(field),
                    value: this.getDefaultValue(field.defaultValue),
                    // value1: this.getDefaultValue(field.defaultValue),
                    entity: field.entity
                }]);
        }
        this.handleTouched();
        this.handleDataChange();
    };
    QueryBuilderComponent.prototype.removeRule = function (rule, parent) {
        if (this.disabled) {
            return;
        }
        parent = parent || this.data;
        if (this.config.removeRule) {
            this.config.removeRule(rule, parent);
        }
        else {
            parent.rules = parent.rules.filter(function (r) { return r !== rule; });
        }
        this.inputContextCache.delete(rule);
        this.operatorContextCache.delete(rule);
        this.fieldContextCache.delete(rule);
        this.entityContextCache.delete(rule);
        this.removeButtonContextCache.delete(rule);
        this.handleTouched();
        this.handleDataChange();
    };
    QueryBuilderComponent.prototype.addRuleSet = function (parent) {
        if (this.disabled) {
            return;
        }
        parent = parent || this.data;
        if (this.config.addRuleSet) {
            this.config.addRuleSet(parent);
        }
        else {
            parent.rules = parent.rules.concat([{ condition: 'and', rules: [] }]);
        }
        this.handleTouched();
        this.handleDataChange();
    };
    QueryBuilderComponent.prototype.removeRuleSet = function (ruleset, parent) {
        if (this.disabled) {
            return;
        }
        ruleset = ruleset || this.data;
        parent = parent || this.parentValue;
        if (this.config.removeRuleSet) {
            this.config.removeRuleSet(ruleset, parent);
        }
        else {
            parent.rules = parent.rules.filter(function (r) { return r !== ruleset; });
        }
        this.handleTouched();
        this.handleDataChange();
    };
    QueryBuilderComponent.prototype.transitionEnd = function (e) {
        this.treeContainer.nativeElement.style.maxHeight = null;
    };
    QueryBuilderComponent.prototype.toggleCollapse = function () {
        var _this = this;
        this.computedTreeContainerHeight();
        setTimeout(function () {
            _this.data.collapsed = !_this.data.collapsed;
        }, 100);
    };
    QueryBuilderComponent.prototype.computedTreeContainerHeight = function () {
        var nativeElement = this.treeContainer.nativeElement;
        if (nativeElement && nativeElement.firstElementChild) {
            nativeElement.style.maxHeight = (nativeElement.firstElementChild.clientHeight + 8) + 'px';
        }
    };
    QueryBuilderComponent.prototype.changeCondition = function (value) {
        if (this.disabled) {
            return;
        }
        this.data.condition = value;
        this.handleTouched();
        this.handleDataChange();
    };
    QueryBuilderComponent.prototype.changeOperator = function (rule) {
        console.log(rule)
        if (this.disabled) {
            return;
        }
        if (this.config.coerceValueForOperator) {
            rule.value = this.config.coerceValueForOperator(rule.operator, rulRulee.value, rule);
        }
        else {
            rule.value = this.coerceValueForOperator(rule.operator, rule.value, rule);
        }
        this.handleTouched();
        this.handleDataChange();
    };
    QueryBuilderComponent.prototype.coerceValueForOperator = function (operator, value, rule) {
        console.log(operator);
        var inputType = this.getInputType(rule.field, operator);
        if (inputType === 'multiselect' && !Array.isArray(value)) {
            return [value];
        }
        return value;
    };
    QueryBuilderComponent.prototype.changeInput = function () {
        if (this.disabled) {
            return;
        }
        this.handleTouched();
        this.handleDataChange();
    };
    QueryBuilderComponent.prototype.changeField = function (fieldValue, rule) {
        console.log(rule);
        if (this.disabled) {
            return;
        }

        var field = this.config.fields[fieldValue];
        if (field && field.defaultValue !== undefined) {
            rule.value = this.getDefaultValue(field.defaultValue);
        }
        else {
            delete rule.value;
        }
        rule.operator = this.getDefaultOperator(field);
        // Create new context objects so templates will automatically update
        this.inputContextCache.delete(rule);
        this.operatorContextCache.delete(rule);
        this.fieldContextCache.delete(rule);
        this.entityContextCache.delete(rule);
        this.getInputContext(rule);
        this.getFieldContext(rule);
        this.getOperatorContext(rule);
        this.getEntityContext(rule);
        this.handleTouched();
        this.handleDataChange();
    };
    QueryBuilderComponent.prototype.changeEntity = function (entityValue, rule, index, data) {
        if (this.disabled) {
            return;
        }
        var entity = this.entities.find(function (e) { return e.value === entityValue; });
        var defaultField = this.getDefaultField(entity);
        console.log(defaultField.value);
        data.rules[index] = __assign({}, rule, { field: defaultField.value });
        if (defaultField) {
            this.changeField(defaultField.value, __assign({}, rule, { field: defaultField.value }));
        }
        else {
            this.handleTouched();
            this.handleDataChange();
        }
    };
    QueryBuilderComponent.prototype.getDefaultValue = function (defaultValue) {
        switch (typeof defaultValue) {
            case 'function':
                return defaultValue();
            default:
                return defaultValue;
        }
    };
    QueryBuilderComponent.prototype.getOperatorTemplate = function () {
        var t = this.parentOperatorTemplate || this.operatorTemplate;
        return t ? t.template : null;
    };
    QueryBuilderComponent.prototype.getFieldTemplate = function () {
        var t = this.parentFieldTemplate || this.fieldTemplate;
        return t ? t.template : null;
    };
    QueryBuilderComponent.prototype.getEntityTemplate = function () {
        var t = this.parentEntityTemplate || this.entityTemplate;
        return t ? t.template : null;
    };
    QueryBuilderComponent.prototype.getArrowIconTemplate = function () {
        var t = this.parentArrowIconTemplate || this.arrowIconTemplate;
        return t ? t.template : null;
    };
    QueryBuilderComponent.prototype.getButtonGroupTemplate = function () {
        var t = this.parentButtonGroupTemplate || this.buttonGroupTemplate;
        return t ? t.template : null;
    };
    QueryBuilderComponent.prototype.getSwitchGroupTemplate = function () {
        var t = this.parentSwitchGroupTemplate || this.switchGroupTemplate;
        return t ? t.template : null;
    };
    QueryBuilderComponent.prototype.getRemoveButtonTemplate = function () {
        var t = this.parentRemoveButtonTemplate || this.removeButtonTemplate;
        return t ? t.template : null;
    };
    QueryBuilderComponent.prototype.getEmptyWarningTemplate = function () {
        var t = this.parentEmptyWarningTemplate || this.emptyWarningTemplate;
        return t ? t.template : null;
    };
    QueryBuilderComponent.prototype.getQueryItemClassName = function (local) {
        var cls = this.getClassNames('row', 'connector', 'transition');
        cls += ' ' + this.getClassNames(local.ruleset ? 'ruleSet' : 'rule');
        if (local.invalid) {
            cls += ' ' + this.getClassNames('invalidRuleSet');
        }
        return cls;
    };
    QueryBuilderComponent.prototype.getButtonGroupContext = function () {
        if (!this.buttonGroupContext) {
            this.buttonGroupContext = {
                addRule: this.addRule.bind(this),
                addRuleSet: this.allowRuleset && this.addRuleSet.bind(this),
                removeRuleSet: this.allowRuleset && this.parentValue && this.removeRuleSet.bind(this),
                getDisabledState: this.getDisabledState,
                $implicit: this.data
            };
        }
        return this.buttonGroupContext;
    };
    QueryBuilderComponent.prototype.getRemoveButtonContext = function (rule) {
        if (!this.removeButtonContextCache.has(rule)) {
            this.removeButtonContextCache.set(rule, {
                removeRule: this.removeRule.bind(this),
                getDisabledState: this.getDisabledState,
                $implicit: rule
            });
        }
        return this.removeButtonContextCache.get(rule);
    };
    QueryBuilderComponent.prototype.getFieldContext = function (rule) {
        if (!this.fieldContextCache.has(rule)) {
            this.fieldContextCache.set(rule, {
                onChange: this.changeField.bind(this),
                getFields: this.getFields.bind(this),
                getDisabledState: this.getDisabledState,
                fields: this.fields,
                $implicit: rule
            });
        }
        return this.fieldContextCache.get(rule);
    };
    QueryBuilderComponent.prototype.getEntityContext = function (rule) {
        if (!this.entityContextCache.has(rule)) {
            this.entityContextCache.set(rule, {
                onChange: this.changeEntity.bind(this),
                getDisabledState: this.getDisabledState,
                entities: this.entities,
                $implicit: rule
            });
        }
        return this.entityContextCache.get(rule);
    };
    QueryBuilderComponent.prototype.getSwitchGroupContext = function () {
        return {
            onChange: this.changeCondition.bind(this),
            getDisabledState: this.getDisabledState,
            $implicit: this.data
        };
    };
    QueryBuilderComponent.prototype.getArrowIconContext = function () {
        return {
            getDisabledState: this.getDisabledState,
            $implicit: this.data
        };
    };
    QueryBuilderComponent.prototype.getEmptyWarningContext = function () {
        return {
            getDisabledState: this.getDisabledState,
            message: this.emptyMessage,
            $implicit: this.data
        };
    };
    QueryBuilderComponent.prototype.getOperatorContext = function (rule) {
        if (!this.operatorContextCache.has(rule)) {
            this.operatorContextCache.set(rule, {
                onChange: this.changeOperator.bind(this),
                getDisabledState: this.getDisabledState,
                operators: this.getOperators(rule.field),
                $implicit: rule
            });
        }
        return this.operatorContextCache.get(rule);
    };
    QueryBuilderComponent.prototype.getInputContext = function (rule) {
    
        console.log(rule);
        if (!this.inputContextCache.has(rule)) {
            this.inputContextCache.set(rule, {
                onChange: this.changeInput.bind(this),
                getDisabledState: this.getDisabledState,
                options: this.getOptions(rule.field),
                field: this.config.fields[rule.field],
                $implicit: rule
            });
        }
        return this.inputContextCache.get(rule);
    };
    QueryBuilderComponent.prototype.checkEmptyRuleInRuleset = function (ruleset) {
        var _this = this;
        if (!ruleset || !ruleset.rules || ruleset.rules.length === 0) {
            return true;
        }
        else {
            return ruleset.rules.some(function (item) {
                if (item.rules) {
                    return _this.checkEmptyRuleInRuleset(item);
                }
                else {
                    return false;
                }
            });
        }
    };
    QueryBuilderComponent.prototype.validateRulesInRuleset = function (ruleset, errorStore) {
        var _this = this;
        if (ruleset && ruleset.rules && ruleset.rules.length > 0) {
            ruleset.rules.forEach(function (item) {
                if (item.rules) {
                    return _this.validateRulesInRuleset(item, errorStore);
                }
                else if (item.field) {
                    var field = _this.config.fields[item.field];
                    if (field && field.validator && field.validator.apply) {
                        var error = field.validator(item, ruleset);
                        if (error != null) {
                            errorStore.push(error);
                        }
                    }
                }
            });
        }
    };
    QueryBuilderComponent.prototype.handleDataChange = function () {
        this.changeDetectorRef.markForCheck();
        if (this.onChangeCallback) {
            this.onChangeCallback();
        }
        if (this.parentChangeCallback) {
            this.parentChangeCallback();
        }
    };
    QueryBuilderComponent.prototype.handleTouched = function () {
        if (this.onTouchedCallback) {
            this.onTouchedCallback();
        }
        if (this.parentTouchedCallback) {
            this.parentTouchedCallback();
        }
    };
    QueryBuilderComponent.decorators = [
        { type: Component, args: [{
                    selector: 'query-builder',
                    template: "\n    <div [ngClass]=\"getClassNames('switchRow')\">\n      <ng-template #defaultArrowIcon>\n        <i [ngClass]=\"getClassNames('arrowIcon')\"></i>\n      </ng-template>\n\n      <a *ngIf=\"allowCollapse\" (click)=\"toggleCollapse()\" [ngClass]=\"getClassNames('arrowIconButton', data.collapsed ? 'collapsed' : null)\">\n        <ng-container *ngIf=\"getArrowIconTemplate() as template; else defaultArrowIcon\">\n          <ng-container *ngTemplateOutlet=\"template; context: getArrowIconContext()\"></ng-container>\n        </ng-container>\n      </a>\n\n      <ng-container *ngIf=\"getButtonGroupTemplate() as template; else defaultButtonGroup\">\n        <div [ngClass]=\"getClassNames('buttonGroup', 'rightAlign')\">\n          <ng-container *ngTemplateOutlet=\"template; context: getButtonGroupContext()\"></ng-container>\n        </div>\n      </ng-container>\n\n      <ng-template #defaultButtonGroup>\n        <div [ngClass]=\"getClassNames('buttonGroup', 'rightAlign')\">\n          <button type=\"button\" (click)=\"addRule()\" [ngClass]=\"getClassNames('button')\" [disabled]=disabled>\n            <i [ngClass]=\"getClassNames('addIcon')\"></i> Add Rule\n          </button>\n          <button type=\"button\" (click)=\"addRuleSet()\" [ngClass]=\"getClassNames('button')\" *ngIf=\"allowRuleset\" [disabled]=disabled>\n            <i [ngClass]=\"getClassNames('addIcon')\"></i> Add group\n          </button>\n          <ng-container *ngIf=\"!!parentValue && allowRuleset\">\n            <button type=\"button\" (click)=\"removeRuleSet()\" [ngClass]=\"getClassNames('removeButton')\" [disabled]=disabled>\n              <i [ngClass]=\"getClassNames('removeIcon')\"></i>\n  Delete          </button>\n          </ng-container>\n        </div>\n      </ng-template>\n\n      <ng-container *ngIf=\"getSwitchGroupTemplate() as template; else defaultSwitchGroup\">\n        <ng-container *ngTemplateOutlet=\"template; context: getSwitchGroupContext()\"></ng-container>\n      </ng-container>\n\n      <ng-template #defaultSwitchGroup>\n        <div [ngClass]=\"getClassNames('switchGroup', 'transition')\" *ngIf=\"data\">\n          <div [ngClass]=\"getClassNames('switchControl')\">\n            <input type=\"radio\" [ngClass]=\"getClassNames('switchRadio')\" [(ngModel)]=\"data.condition\" [disabled]=disabled\n              value=\"AND\" #andOption />\n            <label (click)=\"changeCondition(andOption.value)\" [ngClass]=\"getClassNames('switchLabel')\">AND</label>\n          </div>\n          <div [ngClass]=\"getClassNames('switchControl')\">\n            <input type=\"radio\" [ngClass]=\"getClassNames('switchRadio')\" [(ngModel)]=\"data.condition\" [disabled]=disabled\n              value=\"or\" #orOption />\n            <label (click)=\"changeCondition(orOption.value)\" [ngClass]=\"getClassNames('switchLabel')\">OR</label>\n          </div>\n        </div>\n      </ng-template>\n    </div>\n\n    <div #treeContainer (transitionend)=\"transitionEnd($event)\" [ngClass]=\"getClassNames('treeContainer', data.collapsed ? 'collapsed' : null)\">\n      <ul [ngClass]=\"getClassNames('tree')\" *ngIf=\"data && data.rules\">\n        <ng-container *ngFor=\"let rule of data.rules;let i=index\">\n\n          <ng-container *ngIf=\"{ruleset: !!rule.rules, invalid: !config.allowEmptyRulesets && rule.rules && rule.rules.length === 0} as local\">\n            <li [ngClass]=\"getQueryItemClassName(local)\">\n              <ng-container *ngIf=\"!local.ruleset\">\n\n                <ng-container *ngIf=\"getRemoveButtonTemplate() as template; else defaultRemoveButton\">\n                  <div [ngClass]=\"getClassNames('buttonGroup', 'rightAlign')\">\n                    <ng-container *ngTemplateOutlet=\"template; context: getRemoveButtonContext(rule)\"></ng-container>\n                  </div>\n                </ng-container>\n\n                <ng-template #defaultRemoveButton>\n                  <div [ngClass]=\"getClassNames('removeButtonSize', 'rightAlign')\">\n                    <button type=\"button\" [ngClass]=\"getClassNames('removeButton')\" (click)=\"removeRule(rule, data)\" [disabled]=disabled>\n                      <i [ngClass]=\"getClassNames('removeIcon')\"></i>\n    Delete                </button>\n                  </div>\n                </ng-template>\n\n                <div *ngIf=\"entities?.length > 0\" class=\"q-inline-block-display\">\n                  <ng-container *ngIf=\"getEntityTemplate() as template; else defaultEntity\">\n                    <ng-container *ngTemplateOutlet=\"template; context: getEntityContext(rule)\"></ng-container>\n                  </ng-container>\n                </div>\n\n                <ng-template #defaultEntity>\n                  <div [ngClass]=\"getClassNames('entityControlSize')\">\n                    <select [ngClass]=\"getClassNames('entityControl')\" [(ngModel)]=\"rule.entity\" (ngModelChange)=\"changeEntity($event, rule,i,data)\"\n                      [disabled]=\"disabled\">\n                      <option *ngFor=\"let entity of entities\" [ngValue]=\"entity.value\">\n                        {{entity.name}}\n                      </option>\n                    </select>\n                  </div>\n                </ng-template>\n\n                <ng-container *ngIf=\"getFieldTemplate() as template; else defaultField\">\n                  <ng-container *ngTemplateOutlet=\"template; context: getFieldContext(rule)\"></ng-container>\n                </ng-container>\n\n                <ng-template #defaultField>\n                  <div [ngClass]=\"getClassNames('fieldControlSize')\">\n                    <select [ngClass]=\"getClassNames('fieldControl')\" [(ngModel)]=\"rule.field\" (ngModelChange)=\"changeField($event, rule)\"\n                      [disabled]=\"disabled\">\n                      <option *ngFor=\"let field of getFields(rule.entity)\" [ngValue]=\"field.value\">\n                        {{field.name}}\n                      </option>\n                    </select>\n                  </div>\n                </ng-template>\n\n                <ng-container *ngIf=\"getOperatorTemplate() as template; else defaultOperator\">\n                  <ng-container *ngTemplateOutlet=\"template; context: getOperatorContext(rule)\"></ng-container>\n                </ng-container>\n\n                <ng-template #defaultOperator>\n                  <div [ngClass]=\"getClassNames('operatorControlSize')\">\n                    <select [ngClass]=\"getClassNames('operatorControl')\" [(ngModel)]=\"rule.operator\" (ngModelChange)=\"changeOperator(rule)\"\n                      [disabled]=\"disabled\">\n                      <option *ngFor=\"let operator of getOperators(rule.field)\" [ngValue]=\"operator\">\n                        {{operator}}\n                      </option>\n                    </select>\n                  </div>\n                </ng-template>\n\n                <ng-container *ngIf=\"findTemplateForRule(rule) as template; else defaultInput\">\n                  <ng-container *ngTemplateOutlet=\"template; context: getInputContext(rule)\"></ng-container>\n                </ng-container>\n\n<ng-template #defaultInput>\n <div [ngClass]=\"getClassNames('inputControlSize')\" [ngSwitch]=\"getInputType(rule.field, rule.operator)\">\n                                                                                                                       <div>\n                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     <input [ngClass]=\"getClassNames('inputControl')\" [(ngModel)]=\"rule.name\" (ngModelChange)=\"changeInput($event)\"\n [disabled]=\"disabled\" *ngSwitchCase=\"'column'\" type=\"text\" placeholder=\"column name\">\n                                                                                                                                                                                                                                                                           <input [ngClass]=\"getClassNames('inputControl')\" [(ngModel)]=\"rule.value\" (ngModelChange)=\"changeInput($event)\"\n [disabled]=\"disabled\" *ngSwitchCase=\"'column'\" type=\"text\" placeholder=\"value\" >\n                                                                                                                                                                                                                                                    </div>\n                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  <input [ngClass]=\"getClassNames('inputControl')\" [(ngModel)]=\"rule.value\" (ngModelChange)=\"changeInput()\"\n [disabled]=\"disabled\" *ngSwitchCase=\"'string'\" type=\"text\">\n  <input [ngClass]=\"getClassNames('inputControl')\" [(ngModel)]=\"rule.value\" (ngModelChange)=\"changeInput()\"\n [disabled]=\"disabled\" *ngSwitchCase=\"'number'\" type=\"number\">\n                   <input [ngClass]=\"getClassNames('inputControl')\" [(ngModel)]=\"rule.value\" (ngModelChange)=\"changeInput()\"\n [disabled]=\"disabled\" *ngSwitchCase=\"'date'\" type=\"date\">\n                    <input [ngClass]=\"getClassNames('inputControl')\" [(ngModel)]=\"rule.value\" (ngModelChange)=\"changeInput()\"\n                      [disabled]=\"disabled\" *ngSwitchCase=\"'time'\" type=\"time\">\n                    <select [ngClass]=\"getClassNames('inputControl')\" [(ngModel)]=\"rule.value\" (ngModelChange)=\"changeInput()\"\n                      [disabled]=\"disabled\" *ngSwitchCase=\"'category'\">\n                      <option *ngFor=\"let opt of getOptions(rule.field)\" [ngValue]=\"opt.value\">\n                        {{opt.name}}\n                      </option>\n                    </select>\n                    <ng-container *ngSwitchCase=\"'multiselect'\">\n                      <select [ngClass]=\"getClassNames('inputControl')\" [(ngModel)]=\"rule.value\" (ngModelChange)=\"changeInput()\"\n                        [disabled]=\"disabled\" multiple>\n                        <option *ngFor=\"let opt of getOptions(rule.field)\" [ngValue]=\"opt.value\">\n                          {{opt.name}}\n                        </option>\n                      </select>\n                    </ng-container>\n                    <input [ngClass]=\"getClassNames('inputControl')\" [(ngModel)]=\"rule.value\" (ngModelChange)=\"changeInput()\"\n                      [disabled]=\"disabled\" *ngSwitchCase=\"'boolean'\" type=\"checkbox\">\n                  </div>\n                </ng-template>\n\n              </ng-container>\n              <query-builder *ngIf=\"local.ruleset\" [data]=\"rule\" [disabled]=\"disabled\" [parentTouchedCallback]=\"parentTouchedCallback || onTouchedCallback\"\n                [parentChangeCallback]=\"parentChangeCallback || onChangeCallback\" [parentInputTemplates]=\"parentInputTemplates || inputTemplates\"\n                [parentOperatorTemplate]=\"parentOperatorTemplate || operatorTemplate\" [parentFieldTemplate]=\"parentFieldTemplate || fieldTemplate\"\n                [parentEntityTemplate]=\"parentEntityTemplate || entityTemplate\" [parentSwitchGroupTemplate]=\"parentSwitchGroupTemplate || switchGroupTemplate\"\n                [parentButtonGroupTemplate]=\"parentButtonGroupTemplate || buttonGroupTemplate\" [parentRemoveButtonTemplate]=\"parentRemoveButtonTemplate || removeButtonTemplate\"\n                [parentEmptyWarningTemplate]=\"parentEmptyWarningTemplate || emptyWarningTemplate\" [parentArrowIconTemplate]=\"parentArrowIconTemplate || arrowIconTemplate\"\n                [parentValue]=\"data\" [classNames]=\"classNames\" [config]=\"config\" [allowRuleset]=\"allowRuleset\"\n                [allowCollapse]=\"allowCollapse\" [emptyMessage]=\"emptyMessage\" [operatorMap]=\"operatorMap\">\n              </query-builder>\n\n              <ng-container *ngIf=\"getEmptyWarningTemplate() as template; else defaultEmptyWarning\">\n                <ng-container *ngIf=\"local.invalid\">\n                  <ng-container *ngTemplateOutlet=\"template; context: getEmptyWarningContext()\"></ng-container>\n                </ng-container>\n              </ng-container>\n\n              <ng-template #defaultEmptyWarning>\n                <p [ngClass]=\"getClassNames('emptyWarning')\" *ngIf=\"local.invalid\">\n                  {{emptyMessage}}\n                </p>\n              </ng-template>\n            </li>\n          </ng-container>\n        </ng-container>\n      </ul>\n    </div>\n  ",

                    styles: ["\n    \uFEFF:host{display:block;width:100%}:host .q-icon{font-style:normal;font-size:12px}:host .q-remove-icon::before{content:'\u274C'}:host .q-arrow-icon-button{float:left;margin:4px 6px 4px 0;transform:rotate(90deg);transition:linear 0.25s transform;cursor:pointer}:host .q-arrow-icon-button.q-collapsed{transform:rotate(0)}:host .q-arrow-icon::before{content:'\u25B6'}:host .q-add-icon{color:#555}:host .q-add-icon::before{content:'\u2795'}:host .q-remove-button{color:#B3415D;width:31px}:host .q-switch-group,:host .q-button-group{font-family:\"Lucida Grande\", Tahoma, Verdana, sans-serif;overflow:hidden}:host .q-right-align{float:right}:host .q-button{margin-left:8px;padding:0 8px;background-color:white}:host .q-button:disabled{display:none}:host .q-control-size{display:inline-block;vertical-align:top;padding-right:10px}:host .q-input-control,:host .q-operator-control,:host .q-field-control,:host .q-entity-control{display:inline-block;padding:5px 8px;color:#555;background-color:#fff;background-image:none;border:1px solid #ccc;border-radius:4px;box-sizing:border-box;width:auto}:host .q-input-control:disabled,:host .q-operator-control:disabled,:host .q-field-control:disabled,:host .q-entity-control:disabled{border-color:transparent}:host .q-operator-control,:host .q-field-control,:host .q-entity-control,:host .q-input-control:not([type='checkbox']){min-height:32px;-webkit-appearance:none}:host .q-switch-label,:host .q-button{float:left;margin-bottom:0;font-size:13px;line-height:30px;font-weight:normal;text-align:center;text-shadow:none;border:1px solid rgba(0,0,0,0.2);box-sizing:border-box}:host .q-switch-label:hover,:host .q-button:hover{cursor:pointer;background-color:#F0F0F0}:host .q-switch-label{background-color:#e4e4e4;padding:0 8px}:host .q-switch-radio{position:absolute;clip:rect(0, 0, 0, 0);height:1px;width:1px;border:0;overflow:hidden}:host .q-switch-radio:checked+.q-switch-label{border:1px solid #619ed7;background:white;color:#3176b3}:host .q-switch-radio:disabled+.q-switch-label{display:none}:host .q-switch-radio:checked:disabled+.q-switch-label{display:initial;color:initial;cursor:default;border-color:transparent}:host .q-invalid-ruleset{border:1px solid rgba(179,65,93,0.5) !important;background:rgba(179,65,93,0.1) !important}:host .q-empty-warning{color:#8d252e;text-align:center}:host .q-ruleset{border:1px solid #CCC}:host .q-rule{border:1px solid #CCC;background:white}:host .q-transition{-webkit-transition:all 0.1s ease-in-out;-moz-transition:all 0.1s ease-in-out;-ms-transition:all 0.1s ease-in-out;-o-transition:all 0.1s ease-in-out;transition:all 0.1s ease-in-out}:host .q-tree-container{width:100%;overflow:hidden;transition:ease-in 0.25s max-height}:host .q-tree-container.q-collapsed{max-height:0 !important}:host .q-tree{list-style:none;margin:4px 0 2px}:host .q-row{padding:6px 8px;margin-top:6px}:host .q-connector{position:relative}:host .q-connector::before{top:-5px;border-width:0 0 2px 2px}:host .q-connector::after{border-width:0 0 0 2px;top:50%}:host .q-connector::before,:host .q-connector::after{content:'';left:-12px;border-color:#CCC;border-style:solid;width:9px;height:calc(50% + 6px);position:absolute}:host .q-connector:last-child::after{content:none}:host .q-inline-block-display{display:inline-block;vertical-align:top}\n  "],
                    providers: [CONTROL_VALUE_ACCESSOR, VALIDATOR]
                },] },
    ];
    /** @nocollapse */
    QueryBuilderComponent.ctorParameters = function () { return [
        { type: ChangeDetectorRef, },
    ]; };
    QueryBuilderComponent.propDecorators = {
        'disabled': [{ type: Input },],
        'data': [{ type: Input },],
        'allowRuleset': [{ type: Input },],
        'allowCollapse': [{ type: Input },],
        'emptyMessage': [{ type: Input },],
        'classNames': [{ type: Input },],
        'operatorMap': [{ type: Input },],
        'parentValue': [{ type: Input },],
        'config': [{ type: Input },],
        'parentArrowIconTemplate': [{ type: Input },],
        'parentInputTemplates': [{ type: Input },],
        'parentOperatorTemplate': [{ type: Input },],
        'parentFieldTemplate': [{ type: Input },],
        'parentEntityTemplate': [{ type: Input },],
        'parentSwitchGroupTemplate': [{ type: Input },],
        'parentButtonGroupTemplate': [{ type: Input },],
        'parentRemoveButtonTemplate': [{ type: Input },],
        'parentEmptyWarningTemplate': [{ type: Input },],
        'parentChangeCallback': [{ type: Input },],
        'parentTouchedCallback': [{ type: Input },],
        'treeContainer': [{ type: ViewChild, args: ['treeContainer',] },],
        'buttonGroupTemplate': [{ type: ContentChild, args: [QueryButtonGroupDirective,] },],
        'switchGroupTemplate': [{ type: ContentChild, args: [QuerySwitchGroupDirective,] },],
        'fieldTemplate': [{ type: ContentChild, args: [QueryFieldDirective,] },],
        'entityTemplate': [{ type: ContentChild, args: [QueryEntityDirective,] },],
        'operatorTemplate': [{ type: ContentChild, args: [QueryOperatorDirective,] },],
        'removeButtonTemplate': [{ type: ContentChild, args: [QueryRemoveButtonDirective,] },],
        'emptyWarningTemplate': [{ type: ContentChild, args: [QueryEmptyWarningDirective,] },],
        'inputTemplates': [{ type: ContentChildren, args: [QueryInputDirective,] },],
        'arrowIconTemplate': [{ type: ContentChild, args: [QueryArrowIconDirective,] },],
        'value': [{ type: Input },],
        
    };
    return QueryBuilderComponent;
}());
export { QueryBuilderComponent };
//# sourceMappingURL=query-builder.component.js.map
