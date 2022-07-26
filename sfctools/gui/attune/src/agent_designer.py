from PyQt5 import QtWidgets, uic,QtGui
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QFileDialog,QMessageBox,QTableWidgetItem,QAbstractItemView,QListWidgetItem
from PyQt5.QtWebEngineWidgets  import QWebEngineView
import sys
import os
import yaml
import shutil
from pandasmodel import PandasModel
from PyQt5.QtGui import QDesktopServices
import pickle as pkl 
import re
import matplotlib.pyplot as plt

# module for MAMBA interpreter 
from mamba_interpreter import process_mamba
#--


class Property: 
    # data container for "property" 
    
    def __init__(self,name,docstr,content):
        self.name = name 
        self.docstr = docstr 
        self.content = content 
    
    def to_string(self):
        # converts this property definition to a python-readable code chunk
        return "        " + "self.%s = %s # %s\n" % (self.name , self.processed_content,self.docstr.replace("\n","."))
    
    @property 
    def processed_content(self):
        # pre-process the content wih mamba intepreter 
        ka,transactions_import, my_interp = process_mamba(self.content)
        return my_interp 
    
class Action:
    # data container for "action"
    def __init__(self,name,docstr,content):
        
        self.name = name 
        self.docstr = docstr 
        self.content = content
    
    @property 
    def processed_content(self):
        # pre-process the content wih mamba intepreter 
        ka,transactions_import, my_interp = process_mamba(self.content)
        return my_interp 
    
    @property
    def transactions_content(self):
        ka,transactions_import, my_interp = process_mamba(self.content)
        return transactions_import
        
    @property
    def ka(self): # list of known agents 
        ka,transactions_import, my_interp = process_mamba(self.content)
        return ka
        
        
class AgentType:

    def __init__(self, name, actions, properties, links):
        self.name = name 
        self.actions = actions 
        self.properties = properties
        self.links = links 

    def to_string(self):
        """
        converts this agnet definition to a python-readable code chunk
        """
        
        # construct dictionary of known agents 
        known_agents_str = "{"
        known_agents = []
        if self.actions is not None:
            for action in self.actions.values():
                known_agents += action.ka 
        known_agents = list(set(known_agents))
        
        for i in known_agents:
            known_agents_str += "'%s': World().get_agents_of_type('%s')[0],\n           " % (i,i)
            # TODO ^ fix for multi agent case here 
            
        known_agents_str += "}\n"
        
        s = "" 
        
        if self.actions is not None:
            my_trans_cont = []
            for action in self.actions.values():
                my_trans_cont += action.transactions_content # + "\n"
            for i in list(set(my_trans_cont)):
                s+= "from transactions import " + str(i) + "\n"
                
        s += """
class %s(Agent):
    def __init__(self):
        super().__init__() # instantiate super class 
        self.known_agents = None 
        
"""% (self.name.capitalize()) #, known_agents_str)

        if self.properties is not None:
            for prop in self.properties.values():
                s += prop.to_string() 
            
            s+= "\n"
        s+= """
    def setup(self):
        self._known_agents = %s 
        
"""    %known_agents_str

        if self.actions is not None:
            for action in self.actions.values():
                s += "\n"
                s += "    def %s(self):\n        \"\"\"\n"  % action.name 
                
                for doc_i in action.docstr.split("\n"):
                    s += "        %s\n" % doc_i 
                    
                s+= "        \"\"\"\n"
                
                for s_i in action.processed_content.split("\n"):
                    s += "        " + s_i + "\n"
            
        print("AGENT TYPE %s _>\n\n" % self.name)
        print(s)
        print("----\n\n")
        
        return s 


class AgentDesigner(QtWidgets.QDialog):
    
    def __init__(self):
        
        super(AgentDesigner, self).__init__() # Call the inherited classes __init__ method
       
        uic.loadUi('agent_designer2.ui', self) # Load the .ui file
        
        self.setFixedSize(self.size());
        
        
        self.AgentTypeLabel.setText("test")
        
        

        # 
        
        self.AddActionButton.pressed.connect(self.add_action)
        self.AddTypeButton.pressed.connect(self.add_agent_type)
        
        self.actionTable.itemSelectionChanged.connect(self.update_action_forms)
        self.propertyTable.itemSelectionChanged.connect(self.update_property_forms)
        
        self.agentTypeList.itemSelectionChanged.connect(self.update_type_list)
        
        self.RemoveTypeButton.pressed.connect(self.remove_agent_type)
        
        self.RenameButton.pressed.connect(self.rename)
        
        self.RemoveActionButton.pressed.connect(self.remove_action)
        self.ActionNameEdit.textChanged.connect(self.update_action_button)
        self.PropertyNameEdit.textChanged.connect(self.update_property_button)
        
        self.AddPropertyButton.pressed.connect(self.add_property)
        
        self.ExportButton.pressed.connect(self.export_python)
        
        self.SaveButton.pressed.connect(self.save_file)
        self.LoadButton.pressed.connect(self.load_file)
        
        self.actionTable.insertColumn(0);
        self.propertyTable.insertColumn(0);
        self.agent_types = {}
        
        self.show()
        
        
    def save_build(self):
        print("save and build")
        
    def export_python(self):
        for agent_type in self.agent_types.values():
            python_str = agent_type.to_string()
        
        
    def load_file(self):
        filename = QFileDialog.getOpenFileName(self, 'Open file',
                                    os.getcwd(), "Agent Files (*.agt)")[0]
        try:
            with open(filename,"rb") as handle:
                self.agent_types = pkl.load(handle)
                
                print("new agent types",self.agent_types)
                # TODO^ warning here 
            
            self.rebuild_type_list()
            
            self.update_action_button()
            self.update_action_forms()
            self.update_action_list()
            
            self.update_property_button()
            self.update_property_forms()
            self.update_property_list()
       
        except:
           print("ERROR ON OPEN FILE")
        
    def save_file(self):
        filename = QFileDialog.getSaveFileName(self, 'Save file',
                                               os.getcwd(), "Agent Files (*.agt)")[0]
        
        with open(filename,"wb") as handle:
            pkl.dump(self.agent_types,handle,protocol=pkl.HIGHEST_PROTOCOL)
        
    def rename(self):
        # rename agent type 
        
        new_name = self.TypelineEdit.text()
        old_name = self.get_selected_agent_type().name
        self.get_selected_agent_type().name  = new_name 
        
        val = self.agent_types[old_name]
        self.agent_types[new_name] = val 
        del self.agent_types[old_name]
        
        
        self.rebuild_type_list()
        
    def remove_agent_type(self):
        # remove current selection 
        
        selected_type = self.get_selected_agent_type()
        del self.agent_types[selected_type.name]
        self.rebuild_type_list()    
        
        
    def update_property_button(self):
        # get current text 
        current_entry = self.PropertyNameEdit.text()
        selected_type = self.get_selected_agent_type()
        
        cond1 = selected_type is not None
        cond2 = selected_type is not None
        
        self.AddPropertyButton.setText("Add")
        self.RemovePropertyButton.setEnabled(False)
        
        if cond1 and cond2:
            if selected_type.properties is not None:
                if current_entry in selected_type.properties:
                    self.AddPropertyButton.setText("Update")
                    self.RemovePropertyButton.setEnabled(True)
       
    
    def update_action_button(self):
        
        # get current text 
        current_entry = self.ActionNameEdit.text()
        selected_type = self.get_selected_agent_type()
        
        cond1 = selected_type is not None
        cond2 = selected_type is not None
        
        
        self.AddActionButton.setText("Add")
        self.RemoveActionButton.setEnabled(False)
        
        if cond1 and cond2:
            if selected_type.actions is not None:
                if current_entry in selected_type.actions:
                    self.AddActionButton.setText("Update")
                    self.RemoveActionButton.setEnabled(True)
       
        
            
        
    def update_action_forms(self):
        # updates all action forms (name, descrition, code)
        
        selected_actions = self.actionTable.selectedItems()
        if selected_actions is not None and len(selected_actions) > 0 and self.get_selected_agent_type() is not None:
            if self.get_selected_agent_type().actions is not None and selected_actions[0].text() in self.get_selected_agent_type().actions:
                current_action = self.get_selected_agent_type().actions[selected_actions[0].text()]
            
                name = current_action.name 
                description = current_action.docstr
                code = current_action.content
            else:
                name = ""
                code = "" 
                description = ""
            self.ActionCodeEdit.setText(code)
            self.ActionNameEdit.setText(name)
            self.ActionDocEdit.setText(description)
        else:
            name = ""
            code = "" 
            description = ""
            self.ActionCodeEdit.setText(code)
            self.ActionNameEdit.setText(name)
            self.ActionDocEdit.setText(description)
      
        self.update_action_button()
    
    def update_property_forms(self):
        
        selected_properties = self.propertyTable.selectedItems()
        if selected_properties is not None and len(selected_properties) > 0 and self.get_selected_agent_type() is not None:
            if self.get_selected_agent_type().properties is not None and selected_properties[0].text() in self.get_selected_agent_type().properties:
                current_property = self.get_selected_agent_type().properties[selected_properties[0].text()]
            
                name = current_property.name 
                description = current_property.docstr
                code = current_property.content
            else:
                name = ""
                code = "" 
                description = ""
            self.PropertyValEdit.setText(code)
            self.PropertyNameEdit.setText(name)
            self.PropertyDocEdit.setText(description)
        else:
            name = ""
            code = "" 
            description = ""
            self.PropertyValEdit.setText(code)
            self.PropertyNameEdit.setText(name)
            self.PropertyDocEdit.setText(description)
      
        self.update_property_button()
    
    
    
    def add_agent_type(self):
        type_name = self.TypelineEdit.text()
        
        if type_name not in self.agent_types:
            new_type = AgentType(type_name,None,None,None)
            self.agent_types[type_name] = new_type
            self.rebuild_type_list()
        else:
            pass 
            # TODO ^ ask for overwrite here 
            
    def get_selected_agent_type(self):
        selected_items = self.agentTypeList.selectedItems()
        if len(selected_items) > 0:
            type_name = selected_items[0].text()
            
            if type_name not in self.agent_types:
                self.agent_types[type_name] = AgentType(None,None,None,None) # create dummy
            
            return self.agent_types[type_name]
            
        else:
            return None 
    
    def update_action_list(self):
        # update current list of actions 
        agent_type = self.get_selected_agent_type()
        
        print("actions of tpye", agent_type)
        if agent_type is not None:
            
            self.actionTable.clear()
            self.actionTable.setRowCount(0)
            
            action_list = self.agent_types[agent_type.name].actions
            print("action list",action_list)
            
            if action_list is not None:
                for i,action in enumerate(action_list):
                    self.actionTable.insertRow(i);
                    #self.actionTable.insertColumn(0);
                    self.actionTable.setItem(i,0,QTableWidgetItem(action_list[action].name));
    
    def update_property_list(self):
        
        agent_type = self.get_selected_agent_type()
        
        print("properties of tpye", agent_type)
        if agent_type is not None:
            
            self.propertyTable.clear()
            self.propertyTable.setRowCount(0)
            
            property_list = self.agent_types[agent_type.name].properties
            print("property list",property_list)
            
            if property_list is not None:
                for i,prop in enumerate(property_list):
                    self.propertyTable.insertRow(i);
                    #self.actionTable.insertColumn(0);
                    self.propertyTable.setItem(i,0,QTableWidgetItem(property_list[prop].name));
    
    
    def remove_action(self):
        # get current selection 
        selected_actions = self.actionTable.selectedItems()
        if len(selected_actions) > 0:
            current_action = selected_actions[0].text()
            
            del self.get_selected_agent_type().actions[current_action]
        
        self.update_action_forms()
        self.update_action_list()
        self.update_action_button()
    
    def rebuild_type_list(self):
    
        selected_items = self.agentTypeList.selectedItems()
        type_name = None 
        
        if len(selected_items) > 0:
            type_name = selected_items[0].text()
            # update name 
            self.AgentTypeLabel.setText(type_name)
        
        self.agentTypeList.clear()
        
        for k, v in self.agent_types.items():
            new_item = QListWidgetItem(str(k))
            self.agentTypeList.addItem(new_item)
            if type_name is not None and str(k) == type_name:
                self.agentTypeList.setCurrentItem(new_item)    # re-select
    
    def update_type_list(self):
        
        selected_items = self.agentTypeList.selectedItems()
        type_name = None 
        
        if len(selected_items) > 0:
            type_name = selected_items[0].text()
            # update name 
            self.AgentTypeLabel.setText(type_name)
        
        
        self.update_action_forms()
        self.update_action_list()
        self.update_action_button()
    
        self.update_property_forms()
        self.update_property_list()
        self.update_property_button()
        
    
    def add_property(self):
        # 
        agent_type = self.get_selected_agent_type()
        if agent_type is None:
            raise TypeError("Could not find agent type for current edit")
        
        if agent_type.properties is None:
            agent_type.properties = {}
        
        property_val = self.PropertyValEdit.toPlainText()
        property_name = self.PropertyNameEdit.text()
        property_doc = self.PropertyDocEdit.toPlainText()
        
        new_property = Property(property_name,property_doc,property_val)
        
        agent_type.properties[new_property.name] = new_property
        
        if self.AddPropertyButton.text() == "Add":
            self.update_property_list()
        self.update_property_button()
            
    def add_action(self):
        # get current agent type
        
        agent_type = self.get_selected_agent_type()
        if agent_type is None:
            raise TypeError("Could not find agent type for current edit")
        
        if agent_type.actions is None:
            agent_type.actions = {}
            
        # read data of this action 
        action_code = self.ActionCodeEdit.toPlainText()
        action_name = self.ActionNameEdit.text()
        action_doc = self.ActionDocEdit.toPlainText()
        
        
        # create new action object 
        new_action = Action(action_name,action_doc,action_code)
        
        #if action_name in agent_type.actions:
        #    del agent_type.actions[action_name] # delete old 
            
            
        agent_type.actions[action_name] = new_action # insert new 
        
        if self.AddActionButton.text() == "Add":
            self.update_action_list()
        self.update_action_button()
        
        
    
    
if __name__ == "__main__":
    """
    """
    
    app = QtWidgets.QApplication(sys.argv)
    # window = ProjectDesigner()
    window = AgentDesigner()
    app.exec_()
