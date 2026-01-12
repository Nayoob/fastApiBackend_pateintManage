from doctest import Example
from os import path
from pydoc import describe
from unittest.mock import patch 
from fastapi import FastAPI, HTTPException , Path,Query 
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.agent import SimpleAgent

from typing import Literal  , Annotated, Optional
from pydantic import BaseModel , Field , computed_field 
import json


app = FastAPI()

agent = SimpleAgent()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Patient(BaseModel):

    id: Annotated[str, Field(..., description='ID of the patient', examples=['P001' , 'p007'])]
    name: Annotated[str, Field(..., description='Name of the patient')]
    city: Annotated[str, Field(..., description='City where the patient is living')]
    age: Annotated[int, Field(..., gt=0, lt=120, description='Age of the patient')]
    gender: Annotated[Literal['male', 'female', 'others'], Field(..., description='Gender of the patient')]
    height: Annotated[float, Field(..., gt=0, description='Height of the patient in mtrs')]
    weight: Annotated[float, Field(..., gt=0, description='Weight of the patient in kgs')]

    @computed_field
    @property
    def bmi(self) -> float:
        bmi = round(self.weight/(self.height**2),2)
        return bmi
    
    @computed_field
    @property
    def verdict(self) -> str:

        if self.bmi < 18.5:
            return 'Underweight'
        elif self.bmi < 25:
            return 'Normal'
        elif self.bmi < 30:
            return 'Normal'
        else:
            return 'Obese'


filePath = 'backend/patients.json'

def show_Data():
    with open(filePath,'r') as file:
        data = json.load(file)
    return data

def save_data(data):
    with open(filePath, 'w') as f:
        json.dump(data, f)


def sortDictionary(data , sort_by, sortOrder='asc'):
    arr = []

    for dic in data.values():
        arr.append(dic[sort_by])

    temp  = True if sortOrder.lower() == 'dsc' else False
    arr.sort(reverse=temp)

    returnedDic = {}
    for var in arr:
        for k, v in data.items():
            if var == v[sort_by]:
                returnedDic[k] = v

    return returnedDic


@app.get("/view")
def show_Patients():
    data = show_Data()
    return data


@app.get("/patient/{patient_id}/name/{name}")
def view_patientt(
    patient_id: str = Path(
        ..., 
        description="Patient id in DB", 
        example="P001"
    ),
    name: str = Path(
        ..., 
        min_length=5, 
        max_length=10, 
        description="name hay bahi", 
        example="sufyan"
    )
):
    data = show_Data()

    if patient_id in data:
        return data[patient_id], name
    else:
        raise HTTPException(
            status_code=404, 
            detail="Patient Not Found"
        )
    
@app.get('/patient/{patient_id}')
def view_patient(patient_id : str = Path(..., description="Patient id in DB" , example='P001')):
    data = show_Data()
    if patient_id in data:

        return data[patient_id]
    else:
        raise HTTPException(status_code=404 , detail='patient Not found')

# @app.get('/sort')
# def sort_patientss(sort_By: str= Query(...,description='sort On the basis of height , weight , bmi') , order: str=Query('asc' , description='sort in asc,dsc')):

#     parameter = ['height' , 'weight' ,'bmi']
#     if sort_By.lower() not in parameter:
#         raise HTTPException(status_code=400 , detail=f'sort as per these parameters{parameter}')
    
#     if order.lower() not in ['asc' , 'dsc' ]:
#         raise HTTPException(status_code=400 , detail="Use asc or dsc only for order!")
    
#     #laod data fron json first
#     data = show_Data()

#     returnedDict = sortDictionary(data , sort_By , order)

#     return returnedDict


@app.get('/sort')
def sort_patients(sort_by: str = Query(..., description='Sort on the basis of height, weight or bmi'), order: str = Query(default='asc', description='sort in asc or desc order')):

    valid_fields = ['height', 'weight', 'bmi']

    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail=f'Invalid field select from {valid_fields}')
    
    if order not in ['asc', 'desc']:
        raise HTTPException(status_code=400, detail='Invalid order select between asc and desc')
    
    data = show_Data()

    sort_order = True if order=='desc' else False

    sorted_data = sorted(data.values(), key = lambda x: x.get(sort_by, 0), reverse=sort_order)

    return sorted_data

# just wondering hwo the agents send responce to frontend from agent-> backned -> frontend 

@app.get('/use_agent')
def call_agent(user_input:str, name:str):
    respose = agent.think(user_input)
    return f"{respose} , {name}"



@app.post('/create')
def create_patient(patient : Patient):
    data = show_Data()

    if patient.id in data:
        raise HTTPException(status_code=400 , detail="patient already exist")

    data[patient.id] = patient.model_dump(exclude={'id'})

    save_data(data)

    return JSONResponse(status_code=201 , content={"message": "patient created Successfully !"})



#pydantic model for updating patient data 

class PatientUpdate(BaseModel):

    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[int], Field(default=None, gt=0)]
    gender: Annotated[Optional[Literal['male', 'female']], Field(default=None)]
    height: Annotated[Optional[float], Field(default=None, gt=0)]
    weight: Annotated[Optional[float], Field(default=None, gt=0)]

 
@app.put('/edit/{patient_id}')
def update_patient(patient_update: PatientUpdate , patient_id: str=Path(..., description="patient id")):

    data = show_Data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail='Patient not found')
    
    existing_patient_info = data[patient_id]

    updated_patient_info = patient_update.model_dump(exclude_unset=True)

    for key, value in updated_patient_info.items():
        existing_patient_info[key] = value

    #existing_patient_info -> pydantic object -> updated bmi + verdict
    existing_patient_info['id'] = patient_id
    patient_pydandic_obj = Patient(**existing_patient_info)
    #-> pydantic object -> dict
    existing_patient_info = patient_pydandic_obj.model_dump(exclude={'id'})

    # add this dict to data
    data[patient_id] = existing_patient_info

    # save data
    save_data(data)

    return JSONResponse(status_code=200, content={'message':'patient updated'})

@app.delete('/delete/{patient_id}')
def delete_patient(patient_id: str):

    # load data
    data = show_Data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail='Patient not found')
    
    del data[patient_id]

    save_data(data)

    return JSONResponse(status_code=200, content={'message':'patient deleted'})

