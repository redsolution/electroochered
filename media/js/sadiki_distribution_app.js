// model function for kindergtn
function KinderGtn(data) {
  var self = this;
  this.display = ko.observable(false);
  this.status = ko.observable('initial');
  this.disabled = ko.observable(false);
  this.messages = ko.observableArray();
  this.allowedStatus = ['initial', 'processing', 'ready'];

  this.id = ko.observable(data.id);
  this.shortName = ko.observable(data.short_name);
  this.ageGroupsIds = ko.observable(data.age_groups);
  this.sadikGroups = ko.observableArray();
  this.activeDistribution = ko.observable(data.active_distribution || false);

  this.addSadikGroup = function(data) {
    var sadikGroup = new SadikGroup(data);
    this.sadikGroups.push(sadikGroup);
    return sadikGroup;
  };

  this.setStatus = function(status) {
    if (self.allowedStatus.indexOf(status) > -1) {
      self.status(status);
    }
  };

  this.isInitial = ko.pureComputed(function() {
    return self.status() == 'initial';
  }, this);

  this.isProcessing = ko.pureComputed(function() {
    return self.status() == 'processing';
  }, this);


  this.isReady = ko.pureComputed(function() {
    return self.status() == 'ready';
  }, this);

  this.fullName = ko.pureComputed(function() {
    if (self.activeDistribution()) {
      return self.shortName();
    } else {
      return self.shortName() + ' - Этот ДОУ не принимает участия в респеделении';
    }
  }, this);

}

function AgeGroup(data) {
  this.id = ko.observable(data.id);
  this.name = ko.observable(data.name);
  this.shortName = ko.observable(data.short_name);
  this.minBirthDate = ko.observable(data.min_birth_date);
  this.maxBirthDate = ko.observable(data.max_birth_date);
}

function SadikGroup(data) {
  self = this;
  this.id = ko.observable(data.id || null);
  this.capacity = ko.observable(data.capacity || 0);
  this.freePlaces = ko.observable(data.free_places || 0).extend({trackChange: true});
  this.ageGroup = ko.observable(data.age_group);
  this.name = ko.observable();

  this.setName = function(ageGroups) {
    var ageGroupId = self.ageGroup();
    var ageGroup = ko.utils.arrayFirst(ageGroups(), function(item) {
      return item.id() === ageGroupId;
    });
    self.name(ageGroup.name());
  };
}

function Message(data) {
  this.msgClass = ko.observable(data.class || 'alert');
  this.message = ko.observable(data.message || '');
}

function KgListViewModel() {
  var self = this;
  this.KinderGtnList = ko.observableArray();
  this.filterText = ko.observable('');

  this.ageGroups = ko.observableArray();
  this.viewStatus = ko.observable();
  this.distributionIsActive = ko.observable(distribution_is_active);

  self.init = function() {
    this.viewStatus("Загружается список ДОУ и данные возрастных групп...");
    var kgxhr = self.loadKinderGtns();
    var agxhr = self.loadAgeGroups();
    $.when(kgxhr, agxhr).done(function() {self.viewStatus('');});
  };

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

  this.showMessage = function(elem) {
    if (elem.nodeType === 1) {
      $(elem).hide().slideDown();
    }
  };

  this.addGroupsToKindergtn = function(kg, data) {
    /* Add groups to kindergtn according to it's array of allowed age groups.
     * First - lookup for proper group data object in passed data array.
     * If no group data for given age group foud, group generated
     * automatically, with default values.
     */

    var errFlag = false;
    $.each(kg.ageGroupsIds(), function(key, val) {
      // ищем подходящую группу среди активных возрастных групп в садике
      sadikGroup = data.filter(function(item) {
        return item.age_group == val;
      });
      // если такая группа есть и она одна - используем её данные
      var sg;
      if (sadikGroup.length == 1) {
        sg = kg.addSadikGroup(sadikGroup[0]);
        sg.setName(self.ageGroups);
      // если таких групп несколько - ошибка, запрещаем работу с ДОУ
      } else if (sadikGroup.length > 1) {
        // kg.display(false);
        errFlag = true;
        kg.messages.push(new Message({
          'class': 'alert',
          'message': 'Данный ДОУ содержит более одной активной группы для ' +
          'определенного возраста. Сообщите о проблеме в техническую поддержку.'
        }));
      // если такой группы нет - создаем новую
      } else {
        sg = kg.addSadikGroup({'age_group': val}, self.ageGroups);
        sg.setName(self.ageGroups);
      }
    });

    kg.display(!errFlag);
  };

  this.getSadikGroups = function(kg) {
    if (kg.isProcessing() || kg.isReady()) {
      return;
    }

    kg.setStatus('processing');

    $.getJSON('/api2/sadik/' + kg.id() + '/groups/', function(data) {
      self.addGroupsToKindergtn(kg, data);
    }).error(function(e) {
      kg.display(false);
      kg.messages.push(new Message({
        'class': 'alert',
        'message': 'Ошибка при попытке загрузить данные о доступных для ' +
                   'зачисления группах. Обновите страницу и попробуйте еще раз'
      }));
      console.log('error while downloading sadikgroups list');
    }).always(function() {
      kg.setStatus('ready');
    });
  };

  this.saveSadikGroups = function(kg) {
    if (kg.disabled()) {
      return;
    }
    // chek if data changed
    var rawData = kg.sadikGroups().filter(function(item){return item.freePlaces.isChanged()});
    if (rawData.length) {
      kg.disabled(true);
      var data = ko.toJSON(rawData);
      $.post('/api2/sadik/' + kg.id() + '/groups/', data, function(returnedData) {
        kg.sadikGroups.removeAll();
        self.addGroupsToKindergtn(kg, returnedData);
        kg.messages.push(new Message({'class': 'alert-success', 'message': 'Данные успешно сохранены'}));
      }).always(function() {
        kg.disabled(false);
      });
    } else {
      kg.messages.push(new Message({'class': 'alert-info', 'message': 'Данные не изменялись'}));
    }
  };

  // downloading json of kindergartens objects
  self.loadKinderGtns = function() {
    var xhr = $.getJSON('/api2/sadik/simple_info/', function(data) {
      $.each(data, function(key, val) {
        self.KinderGtnList.push(new KinderGtn(val));
      });
    }).error(function(e) {
      console.log('error while downloading kindergtns list');
    });
    return xhr;
  };

  self.loadAgeGroups = function() {
    // downloading json of agegroups objects
    var xhr = $.getJSON('/api2/age_groups/', function(data) {
      $.each(data, function(key, val) {
        self.ageGroups.push(new AgeGroup(val));
      });
    }).error(function(e) {
      console.log('error while downloading agegroups list');
    });
    return xhr;
  };
}

vm = new KgListViewModel();
ko.applyBindings(vm);

vm.init();

ko.bindingHandlers.highlightedText = {
  update: function(element, valueAccessor) {
    var options = valueAccessor();
    var value = ko.utils.unwrapObservable(options.text);
    var search = ko.utils.unwrapObservable(options.highlight);
    // remove previous highlight, if no filter value present
    if (search.length === 0) {
      element.innerHTML = value;
      return;
    }
    // could do this or something similar to escape HTML before replacement,
    // if there is a risk of HTML injection in this value
    if (options.sanitize) {
      value = $('<div/>').text(value).html();
    }
    var re = new RegExp(search, 'ig');
    // if found matches - highlighting them
    var match = value.match(re);
    if (match) {
      var replacement = '<span class="highlight">' + match[0] + '</span>';
      element.innerHTML = value.replace(re, replacement);
    }
  }
};

/** Binding to make content appear with 'slide' effect */
ko.bindingHandlers.slideOn = {
    update: function(element, valueAccessor) {
        var options = valueAccessor();
        if(options() === true) {
          $(element).hide().slideDown('slow');
        } else {
          $(element).hide();
        }
    }
};

ko.extenders.trackChange = function (target, track) {
    if (track) {
        target.isChanged = ko.observable(false);
        target.originalValue = target();
        target.subscribe(function (newValue) {
            // use != not !== so numbers will equate naturally
            target.isChanged(newValue != target.originalValue);
        });
    }
    return target;
};



// This function gets cookie with a given name
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');

/*
The functions below will create a header with csrftoken
*/

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
function sameOrigin(url) {
    // test that a given url is a same-origin URL
    // url could be relative or scheme relative or absolute
    var host = document.location.host; // host + port
    var protocol = document.location.protocol;
    var sr_origin = '//' + host;
    var origin = protocol + sr_origin;
    // Allow absolute or scheme relative URLs to same origin
    return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
        (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
        // or any other URL that isn't scheme relative or absolute i.e relative.
        !(/^(\/\/|http:|https:).*/.test(url));
}

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
            // Send the token to same-origin, relative URLs only.
            // Send the token only if the method warrants CSRF protection
            // Using the CSRFToken value acquired earlier
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});
