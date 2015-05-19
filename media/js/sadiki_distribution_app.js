// model function for kindergtn
function KinderGtn(data) {
  this.id = ko.observable(data.id);
  this.shortName = ko.observable(data.short_name);
  this.ageGroupsIds = ko.observable(data.age_groups);
  this.ageGroups = ko.observableArray([]);
}

function AgeGroup(data) {
  this.id = ko.observable(data.id);
  this.name = ko.observable(data.name);
  this.shortName = ko.observable(data.short_name);
  this.minBirthDate = ko.observable(data.min_birth_date);
  this.maxBirthDate = ko.observable(data.max_birth_date);
}

function KgListViewModel() {
  var self = this;
  this.KinderGtnList = ko.observableArray([]);
  this.filterText = ko.observable('');

  this.ageGroups = ko.observableArray([]);

  // selecting kindergartens to show on the page, filtering them
  this.kindergtnsToShow = ko.pureComputed(function() {
    var text = this.filterText().toLowerCase();
    if (text) {
      return ko.utils.arrayFilter(this.KinderGtnList(), function(kg) {
        return kg.shortName().toLowerCase().indexOf(text) > -1;
      });
    }
    return this.KinderGtnList();
  }, this);

  this.getAgeGroups = function(kg) {
    kg.ageGroups.removeAll();
    kg.ageGroupsIds().forEach(function(val) {
      var val = val;
      var ageGroup = ko.utils.arrayFirst(self.ageGroups(), function(item) {
        return val === item.id();;
      });
      kg.ageGroups.push(ageGroup);
    });
  };

  // downloading json of kindergartens objects
  $.getJSON('/api2/get_simple_kg_info/', function(data) {
    $.each(data, function(key, val) {
      self.KinderGtnList.push(new KinderGtn(val));
    });
  }).error(function(e){
    console.log('error while downloading kindergtns list');
  });

  // downloading json of agegroups objects
  $.getJSON('/api2/age_groups/', function(data) {
    $.each(data, function(key, val) {
      self.ageGroups.push(new AgeGroup(val));
    });
  }).error(function(e){
    console.log('error while downloading agegroups list');
  });
}

ko.applyBindings(new KgListViewModel());
